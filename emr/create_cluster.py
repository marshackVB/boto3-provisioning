"""
Class that creates a EMR cluster from a yaml configuration file. Yaml config file
is passed as an argument to the script.

Adapted from https://medium.com/@datitran/quickstart-pyspark-with-anaconda-on-aws-660252b88c9a
"""

import boto3
import botocore
import yaml
import time
import logging
import os

# Logging to the terminal
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class EMRLoader():

    def __init__(self, config):
        self.aws_access_key = config.get('aws_access_key')
        self.aws_secret_access_key = config.get('aws_secret_access_key')
        self.region_name = config.get('region_name')
        self.cluster_name = config.get('cluster_name')
        self.instance_count = config.get('instance_count')
        self.master_instance_type = config.get('master_instance_type')
        self.slave_instance_type = config.get('slave_instance_type')
        self.key_name = config.get('key_name')
        self.subnet_id = config.get('subnet_id')
        self.log_uri = config.get('log_uri')
        self.software_version = config.get('software_version')
        self.script_bucket_name = config.get('script_bucket_name')
        self.bootstrap_path = config.get('bootstrap_path')
        self.cluster_bootstrap_script = config.get('cluster_bootstrap_script')
        self.master_bootstrap_script = config.get('master_bootstrap_script')


    def boto_client(self, service):
        """Provide credentials to boto3 client"""
        client = boto3.client(service,
                              aws_access_key_id=self.aws_access_key,
                              aws_secret_access_key=self.aws_secret_access_key,
                              region_name=self.region_name)
        return client


    def load_cluster(self):
        """Instantiate the boto3 client"""
        response = self.boto_client("emr").run_job_flow(
            Name=self.cluster_name,
            LogUri=self.log_uri,
            ReleaseLabel=self.software_version,
            Instances={
                'MasterInstanceType': self.master_instance_type,
                'SlaveInstanceType': self.slave_instance_type,
                'InstanceCount': self.instance_count,
                'KeepJobFlowAliveWhenNoSteps': True,
                'TerminationProtected': False,
                'Ec2KeyName': self.key_name,
                'Ec2SubnetId': self.subnet_id
            },
            Applications=[
                {
                    'Name': 'Spark'
                },
                {
                    'Name': 'Hive'
                }
            ],
            BootstrapActions=[
                {
                    'Name': 'Install Conda',
                    'ScriptBootstrapAction': {
                        'Path': 's3://{bucket_name}/{script_name}'.format(bucket_name=self.script_bucket_name,
                                                                          script_name=self.cluster_bootstrap_script)
                    }
                },
            ],
            Configurations = [
                {
                    "Classification": "spark-hive-site",
                    "Properties": {"hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                    }
                }
            ],

            VisibleToAllUsers=True,
            JobFlowRole='EMR_EC2_DefaultRole',
            ServiceRole='EMR_DefaultRole'
        )

        logger.info(response)
        return response


    def add_step(self, job_flow_id, master_dns):
        response = self.boto_client("emr").add_job_flow_steps(
            JobFlowId=job_flow_id,
            Steps=[
                {
                    'Name': 'setup - copy files',
                    'ActionOnFailure': 'CANCEL_AND_WAIT',
                    'HadoopJarStep': {
                        'Jar': 'command-runner.jar',
                        'Args': ['aws', 's3', 'cp',
                                 's3://{bucket_name}/{script_name}'.format(bucket_name=self.script_bucket_name,
                                                                           script_name=self.master_bootstrap_script),
                                 '/home/hadoop/']
                    }
                },
                {
                    'Name': 'setup pyspark with conda',
                    'ActionOnFailure': 'CANCEL_AND_WAIT',
                    'HadoopJarStep': {
                        'Jar': 'command-runner.jar',
                        'Args': ['sudo', 'bash', '/home/hadoop/{script_name}'.format(script_name=self.master_bootstrap_script), master_dns]
                    }
                }
            ]
        )

        logger.info(response)
        return response


    def upload_to_s3(self):
        """Load bootstrap scripts to an S3 bucket. If the bucket doesnt exist,
        create it.
        """
        s3 = self.boto_client("s3")
        try:
            s3.head_bucket(Bucket=self.script_bucket_name)
        except:
            s3.create_bucket(Bucket=self.script_bucket_name)

        cluster_bootstrap_path = self.bootstrap_path + self.cluster_bootstrap_script
        master_bootstrap_path = self.bootstrap_path + self.master_bootstrap_script

        s3.upload_file(cluster_bootstrap_path, self.script_bucket_name, self.cluster_bootstrap_script)
        s3.upload_file(master_bootstrap_path, self.script_bucket_name, self.master_bootstrap_script)


    def create_cluster(self):
        """Run all the necessary steps to create the cluster and run all
        bootstrap operations.
        """

        # Upload bootstrap scripts to S3
        self.upload_to_s3()

         # Launch the cluster
        emr_response = self.load_cluster()
        emr_client = self.boto_client("emr")

         # Monitor cluster creation. Once it is up an running, run the master
         # node bootstrap script
        while True:

            job_response = emr_client.describe_cluster(ClusterId=emr_response.get("JobFlowId"))

            # Monitoring the cluster creation job status every 10 seconds
            time.sleep(10)

            if job_response.get("Cluster").get("MasterPublicDnsName") is not None:
                master_dns = job_response.get("Cluster").get("MasterPublicDnsName")

            # Getting job status
            job_state = job_response.get("Cluster").get("Status").get("State")
            job_state_reason = job_response.get("Cluster").get("Status").get("StateChangeReason").get("Message")

            # Check if cluster was created succesfully
            if job_state == "WAITING":
                logger.info("Cluster was created")
                cluster_created = True
                break

            # Stop the process if cluster creation failed
            if job_state in ["TERMINATED", "TERMINATED_WITH_ERRORS"]:
                logger.info("Cluster creation failed: {job_state} "
                              "with reason: {job_state_reason}".format(job_state=job_state, job_state_reason=job_state_reason))
                cluster_created = False
                break

        # If cluster creation was sucessful, fun the master node bootstrap script
        if cluster_created:

            logger.info("Running master node boostrap script")

            add_step_response = self.add_step(emr_response.get("JobFlowId"), master_dns)

            while True:
                list_steps_response = emr_client.list_steps(ClusterId=emr_response.get("JobFlowId"),
                                                            StepStates=["COMPLETED"])
                time.sleep(5)

                if len(list_steps_response.get("Steps")) == len(
                        add_step_response.get("StepIds")):  # make sure that all steps are completed
                    logger.info("\nMaster node boostrap complete. Cluster available for use.\n")
                    logger.info("Master DNS: {0}".format(master_dns))
                    break


# Example: python create_cluster.py /home/user/Documents/config.yml
if __name__ == "__main__":
    import argparse

    # Profile the yaml configuarion file as an argument
    parser = argparse.ArgumentParser(description='Configuration file')
    parser.add_argument('config_file')
    args = parser.parse_args()

    with open(args.config_file, "r") as file:
        config = yaml.load(file)

    config_emr = config.get("emr")

    emr_loader = EMRLoader(config_emr)
    emr_loader.create_cluster()
