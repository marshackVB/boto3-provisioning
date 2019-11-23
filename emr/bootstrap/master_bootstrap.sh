# Adapted from...
# https://bytes.babbel.com/en/articles/2017-07-04-spark-with-jupyter-inside-vpc.html
# https://medium.com/@alexjsanchez/python-3-notebooks-on-aws-ec2-in-15-mostly-easy-steps-2ec5e662c6c6

# Set pyspark to open in jupyter notebook
echo "export PYSPARK_DRIVER_PYTHON_OPTS='notebook'" >> /home/hadoop/.bashrc
source home/hadoop/.bashrc

# Create notebok password, replace "99999" with your password of choice
JUPYTER_PASSWORD=${1:-"99999"}
HASHED_PASSWORD=$(python -c "from notebook.auth import passwd; print(passwd('$JUPYTER_PASSWORD'))")

# Create SSL certificate
mkdir /home/hadoop/certs

sudo openssl req -x509 -nodes -days 365 -newkey rsa:1024 \
-subj "/C=GB/ST=London/L=London/O=Org Name/OU=Department Name/CN=Name/emailAddress=myemail@gmail.com" \
-keyout /home/hadoop/certs/mycert.pem  -out /home/hadoop/certs/mycert.pem

# Create jupyter notebook config file
mkdir -p /home/hadoop/.jupyter
touch ls /home/hadoop/.jupyter/jupyter_notebook_config.py

echo "c = get_config()" >> /home/hadoop/.jupyter/jupyter_notebook_config.py

echo "c.NotebookApp.password = u'$HASHED_PASSWORD'" >> /home/hadoop/.jupyter/jupyter_notebook_config.py #This isnt working properly for some reason

echo "c.NotebookApp.open_browser = False" >> /home/hadoop/.jupyter/jupyter_notebook_config.py

echo "c.NotebookApp.ip = '0.0.0.0'" >> /home/hadoop/.jupyter/jupyter_notebook_config.py

echo "c.NotebookApp.certfile = u'/home/hadoop/certs/mycert.pem'" >> /home/hadoop/.jupyter/jupyter_notebook_config.py

echo "c.IPKernelApp.pylab = 'inline'" >> /home/hadoop/.jupyter/jupyter_notebook_config.py
