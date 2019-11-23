"""The user_data parameter in boto3's run instance method requires the
bootstrap actions to be supplied as a string. Additionally, the very first item
must be #!/bin/bash.
"""


user_data= """#!/bin/bash
sudo pip3 install keras --upgrade
JUPYTER_PASSWORD=${1:-"99999"}
HASHED_PASSWORD=$(python -c "from notebook.auth import passwd; print(passwd('$JUPYTER_PASSWORD'))")

mkdir /home/ubuntu/certs

sudo openssl req -x509 -nodes -days 365 -newkey rsa:1024 \
-subj "/C=GB/ST=London/L=London/O=Org Name/OU=Department Name/CN=Name/emailAddress=myemail@gmail.com" \
-keyout /home/ubuntu/certs/mycert.pem  -out /home/ubuntu/certs/mycert.pem

mkdir -p /home/ubuntu/.jupyter
touch ls /home/ubuntu/.jupyter/jupyter_notebook_config.py

echo "c.NotebookApp.password = u'$HASHED_PASSWORD'" >> /home/ubuntu/.jupyter/jupyter_notebook_config.py #This isnt working properly for some reason
echo "c.NotebookApp.open_browser = False" >> /home/ubuntu/.jupyter/jupyter_notebook_config.py
echo "c.NotebookApp.ip = '0.0.0.0'" >> /home/ubuntu/.jupyter/jupyter_notebook_config.py
echo "c.NotebookApp.certfile = u'/home/ubuntu/certs/mycert.pem'" >> /home/ubuntu/.jupyter/jupyter_notebook_config.py
echo "c.IPKernelApp.pylab = 'inline'" >> /home/ubuntu/.jupyter/jupyter_notebook_config.py

jupyter notebook"""
