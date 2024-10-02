import os
import requests
from keystoneauth1.identity import v3
from keystoneauth1.session import Session
import inspect

import openstack
from openstack import connection
from novaclient import client
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


def get_virtual_machines():
    compute_service = conn.compute
    instances = compute_service.servers()
    return instances


def get_id_vm(name):
    virtual_machines = get_virtual_machines()

    for vm in virtual_machines:
        if vm.name == name:
            return vm.id


server = conn.compute.get_server(get_id_vm("aypos_tester9"))

print(server)
# conn.compute.delete_server()


