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
from openstack_configs import *
from configs import *


command = f"source {openrc_loc} && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")


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


command = f"source {openrc_loc} && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

if __name__=='__main__':

    ips_allocated = delete_vms()
# print(ips_allocated)
