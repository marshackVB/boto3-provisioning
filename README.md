## Boto3 infrastructure provisioning scripts for AWS EMR and EC2

This repo contains scripts to provision and bootstrap AWS EMR clusters and GPU-backed EC2 instances using [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html). The boostrap actions install the Conda python distribution on all machines and configure Jupyter notebooks access.  

I have since moved to using [Terrafrom](https://www.terraform.io/) for infrastructure provisioning. It offers a declarative, easier to use syntax, as well as a host of additional, powerful features. It can also be used across multiple cloud service providers.

