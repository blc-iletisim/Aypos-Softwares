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


def get_virtual_machines():
    compute_service = conn.compute
    instances = compute_service.servers()
    return instances


def get_id_vm(name):
    virtual_machines = get_virtual_machines()

    for vm in virtual_machines:
        if vm.name == name:
            return vm


def delete_vms(number):

    for i in range(number):
        # floating_ips = get_floating_ips()
        name_mac = 'aypos_tester' + str(i)
        server = get_id_vm(name_mac)

        server = conn.compute.delete_server(server)


command = "source /home/ubuntu/admin-openrc.sh && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

if __name__=='__main__':

    ips_allocated = delete_vms()
# print(ips_allocated)
