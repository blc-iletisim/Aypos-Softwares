import os
import requests
# from keystoneauth1.identity import v3
# from keystoneauth1.session import Session
import inspect
import openstack
# from openstack import connection
# from novaclient import client

import random
import subprocess
from openstack_configs import *
from configs import *

command = f"source {openrc_loc} && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

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

    network = conn.network.find_network(network_name)

    for i in range(number):
        
        # floating_ips = get_floating_ips()

        randomf = random.randint(0,19)

        flav_name = "aypos.test." + str(randomf)

        flavor = conn.compute.find_flavor(flav_name)

        name_mac = 'aypos_tester' + str(i)

        # give password below
        if use_pem:
            server = conn.compute.create_server(name=name_mac, flavorRef=flavor.id, image_id=image_id,
                                                networks=[{"uuid": network.id}], key_name=pem_file_name)

        else:
            server = conn.compute.create_server(name=name_mac, flavorRef=flavor.id,image_id=image_id,
                                                networks=[{"uuid": network.id}], adminPass=password)

        conn.compute.wait_for_server(server)
        # server.add_floating_ip_to_server(floating_ips[0])
        conn.compute.add_floating_ip_to_server(server, floating_ips[0])
        
        allocated_ips.append(floating_ips[0])

        floating_ips.pop(0)
        
        print(i)

    return allocated_ips


command = f"source {openrc_loc} && env"
proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

# ips_allocated = create_random_vms()
# print(ips_allocated)


