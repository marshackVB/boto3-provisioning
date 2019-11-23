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
import sys

file_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(file_directory)
sys.path.append(parent_directory)


class EC2Loader():

    def __init__(self, config):
        #self.aws_access_key = config.get('aws_access_key')
        #self.aws_secret_access_key = config.get('aws_secret_access_key')
        self.region_name = config.get('region_name')
        self.instance_name = config.get('instance_name')
        self.instance_count = config.get('instance_count')
        self.instance_type = config.get('instance_type')
        self.instance_profile_arn = config.get('instance_profile_arn')
        self.key_name = config.get('key_name')
        self.availability_zone = config.get('availability_zone')
        self.ami = config.get('ami')
        self.ebs_volume_size = config.get('ebs_volume_size')
        self.user_data = config.get('user_data')
        self.security_group_id = config.get('security_group_id')
        self.security_group_name = config.get('security_group_name')

        from bootstrap.gpu_bootstrap import user_data
        self.user_data = user_data


    def boto_client(self, service):
        """Provide credentials to boto3 client"""
        client = boto3.client(service,
                              #aws_access_key_id=self.aws_access_key,
                              #aws_secret_access_key=self.aws_secret_access_key,
                              region_name=self.region_name)
        return client


    def create_instance(self):
        """Instantiate the boto3 client"""
        response = self.boto_client("ec2").run_instances(
        BlockDeviceMappings=[
            { 'DeviceName': '/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': self.ebs_volume_size,
                    'VolumeType': 'gp2',
                },
            },
        ],
        InstanceType= self.instance_type,
        KeyName= self.key_name,
        MinCount=1,
        MaxCount=1,
        ImageId= self.ami,
        UserData=self.user_data,

        Placement={
            'AvailabilityZone': self.availability_zone
        },
        SecurityGroupIds=[
            self.security_group_id
        ],

        DryRun=False,
        IamInstanceProfile={
            'Arn': self.instance_profile_arn,
        },
        InstanceInitiatedShutdownBehavior='terminate',
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'name',
                        'Value': self.instance_name
                    },
                ]
            },
        ],
        )



# Example: python create_gpu_instance.py /home/user/Documents/config.yml
if __name__ == "__main__":
    import argparse

    # Profile the yaml configuarion file as an argument
    parser = argparse.ArgumentParser(description='Configuration file')
    parser.add_argument('config_file')
    args = parser.parse_args()

    with open(args.config_file, "r") as file:
        config = yaml.load(file)

    config_ec2 = config.get("ec2")

    ec2_loader = EC2Loader(config_ec2)
    ec2_loader.create_instance()
