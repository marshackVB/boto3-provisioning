#!/bin/bash

# Install miniconda includes only the Anaconda package installer and Python

# wget conda and save in a bash script with a shorter name
# If the wget operation is successful, then run the bash script
# -b : notify when jobs running in background terminate
# -p : run as Set User ID (SUID) - which allow anyone to accesses the file to access
# it as the owner

# Python 3 latest Anaconda install: https://repo.continuum.io/archive/Anaconda3-5.1.0-Linux-x86_64.sh

wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/conda.sh \
    && /bin/bash ~/conda.sh -b -p $HOME/conda

rm ~/conda.sh


echo -e '\nexport PATH=$HOME/conda/bin:$PATH' >> $HOME/.bashrc && source $HOME/.bashrc

# install packages
conda install -y pandas ipython jupyter pyspark spark-nlp

# set environment variables
echo -e "\nexport PYSPARK_PYTHON=/home/hadoop/conda/bin/python" >> ~/.bashrc
echo "export PYSPARK_DRIVER_PYTHON=/home/hadoop/conda/bin/ipython" >> ~/.bashrc
source ~/.bashrc
