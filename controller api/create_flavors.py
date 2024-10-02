import os
import requests
from keystoneauth1.identity import v3
from keystoneauth1.session import Session

import openstack
from openstack import connection
import random

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
import random


ram_list = [4096, 6144, 5120, 7168]
cpu_list = [2,4,6,7,5]

disk = 8


for i in range(20):
    ram = random.choice(ram_list)
    cpu = random.choice(cpu_list)
    flavor = conn.compute.create_flavor(name="aypos.test."+str(i), ram=ram, vcpus=cpu, disk=disk)
