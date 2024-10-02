import os
import requests
from keystoneauth1.identity import v3
from keystoneauth1.session import Session
import inspect
import openstack
from openstack import connection
from novaclient import client
import random
import subprocess


command = "source /home/ubuntu/admin-openrc.sh && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

os.environ['OS_AUTH_URL'] = "http://10.150.1.251:35357/v3"
os.environ['OS_PROJECT_NAME'] = "admin"
os.environ['OS_USERNAME'] = "admin"
os.environ['OS_PASSWORD'] = "WHMFjzLBHf1N6FxPnZpCDsXYdXewgjsvwju385Mk"
os.environ['OS_USER_DOMAIN_NAME'] = "Default"
os.environ['OS_PROJECT_DOMAIN_NAME']= "Default"

auth_url = os.environ['OS_AUTH_URL']
project_name = os.environ['OS_PROJECT_NAME']
username = os.environ['OS_USERNAME']
password = os.environ['OS_PASSWORD']
user_domain_name = os.environ['OS_USER_DOMAIN_NAME']
project_domain_name = os.environ['OS_PROJECT_DOMAIN_NAME']

# OpenStack ortamýna baðlantý oluþturun
conn = connection.Connection(
    auth_url=auth_url,
    project_name=project_name,
    username=username,
    password=password,
    user_domain_name=user_domain_name,
    project_domain_name=project_domain_name,

)

import re, subprocess



def get_floating_ips():
  # Execute the OpenStack command with error handling
  try:
    command = ["openstack", "floating", "ip", "list"]
    output = subprocess.run(command, capture_output=True, text=True, check=True).stdout
  except subprocess.CalledProcessError as e:
    raise RuntimeError(f"Error executing OpenStack command: {e}") from e

  # Extract IP addresses using regular expression and filtering
  pattern = r"10\.150\.1\.\d+"
  matches = re.findall(pattern, output)

  return matches



def create_random_vms(number):
    
    floating_ips = get_floating_ips()
    allocated_ips = []

    network = conn.network.find_network("Internal")

    for i in range(number):
        
        # floating_ips = get_floating_ips()

        randomf = random.randint(0,19)

        flav_name = "aypos.test." + str(randomf)

        flavor = conn.compute.find_flavor(flav_name)

        name_mac = 'aypos_tester' + str(i)

        server = conn.compute.create_server(name=name_mac, flavorRef=flavor.id,image_id="20944105-1877-4935-bacd-d68dc3691ade",networks=[{"uuid": network.id}],key_name="ayposKeypair")

        conn.compute.wait_for_server(server)
        # server.add_floating_ip_to_server(floating_ips[0])
        conn.compute.add_floating_ip_to_server(server, floating_ips[0])
        
        allocated_ips.append(floating_ips[0])

        floating_ips.pop(0)
        
        print(i)

    return allocated_ips


command = "source /home/ubuntu/admin-openrc.sh && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

# ips_allocated = create_random_vms()
# print(ips_allocated)


