from google.ai.generativelanguage_v1beta import Hyperparameters

from environmentals import *
import re, subprocess
import os, subprocess, inspect, openstack, requests
from keystoneauth1.identity import v3
from keystoneauth1.session import Session
import requests as rq

from flask import Flask, jsonify, request
from configs import *


app = Flask(__name__)


def get_virtual_machines():
    compute_service = conn.compute
    instances = compute_service.servers()
    return instances


def get_id_vm(name):
    virtual_machines = get_virtual_machines()

    for vm in virtual_machines:
        if vm.name == name:
            return vm.id


def start_stress():
    ...


def check_start_server(server_object, server_id):
    status = server_object.status

    if status == 'SHUTOFF':
        conn.compute.start_server(server_id)
        # server = conm.compute.get_server(server_id)
        conn.compute.wait_for_server(server_object)


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

# Example usage (modify output_format as needed)
# ip_addresses = get_floating_ips()


import paramiko

def run_bash_script_on_vm(vm_ip, bash_script, pem_key_path):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=vm_ip, username="ubuntu", key_filename=pem_key_path)

        stdin, stdout, stderr = ssh_client.exec_command(bash_script)

        for line in stdout.readlines():
            print(line.strip())

        ssh_client.close()

    except Exception as e:
        print(f"Error connecting to VM: {e}")


def get_vm_conf():

    # Sanal makineler (örnekler) hakkýnda bilgi alýn
    def get_virtual_machines():
        compute_service = conn.compute
        instances = compute_service.servers()
        print(instances)
        return instances

    def get_vm_by_id(vm_id):

        compute_service = conn.compute
        try:
            vm = compute_service.get_server(vm_id)

            flav = vm.flavor.copy()

            if not use_zone:
                flav["host"] = vm.compute_host
            else:
                flav["host"] = vm.location["zone"] # vm.zone
            #flav['compute_host'] = vm.compute_host
            asd = vm.addresses.copy()

            flav["ip"] = asd[network_name][ip_number]["addr"]

            return vm.name, flav

        except Exception as e:
            print(f"Error retrieving VM with ID {vm_id}: {e}")
            return None, None

    def get_flavors():

        data = {}
        virtual_machines = get_virtual_machines()

        for vm in virtual_machines:

            if not vm:
                continue
            
            print(vm)
            name, flavor = get_vm_by_id(vm.id)
            
            if not name:
                continue

            data[name] = flavor

        return {"result": data}

    return get_flavors()


def get_monitoring_con():

        # Sanal makineler (örnekler) hakkýnda bilgi alýn
    def get_virtual_machines():
        compute_service = conn.compute
        instances = compute_service.servers()
        
        return instances

    def get_vm_by_id(vm_id):

        compute_service = conn.compute
        try:
            vm = compute_service.get_server(vm_id)
            return vm.name, vm.compute_host

        except Exception as e:
            print(f"Error retrieving VM with ID {vm_id}: {e}")
            return None

    def get_flavors():

        virtual_machines = get_virtual_machines()
        con_cd = {}
        lat = {"data": []}
        for vm in virtual_machines:
            
            print(vm)

            name, compute = get_vm_by_id(vm.id)

            if compute in con_cd.keys():
                con_cd[compute].append(name)
            else:
                con_cd[compute] = []

        for i in con_cd:
            lat["data"].append({"virtual_machines": con_cd[i], "host": i})

        return lat

    return get_flavors()


def get_pm_conf(get_all=False):
    # session need sourcing
    def get_host_list(env_vars):
        # Run the openstack command with the captured environment variables
        output = subprocess.run(['openstack', 'hypervisor', 'list'], capture_output=True, text=True, env={**os.environ, **env_vars}).stdout
        print(output)
        rows = output.strip().split("\n")[2:]

        indexes = []
        for row in rows:
            splitted = row.split('|')
            if len(splitted) > 1:
                indexes.append(splitted[1].replace(" ", ""))

        return indexes

    def get_host_details(index, env_vars):
        # Execute the command and capture output
        output = subprocess.run(['openstack', 'hypervisor', 'show', str(index)], capture_output=True, text=True, env={**os.environ, **env_vars}).stdout

        data = {}
        for line in output.strip().split("\n"):
            splitted = line.split("|")
            if len(splitted) < 2:
                continue

            wout0 = splitted[1].replace(" ", "")
            wout1 = splitted[2].replace(" ", "")
            
            print(wout0)
            print(wout1)
            if wout0 == "aggregates":
                wout1 = wout1[2:len(wout1)-2]
                data[wout0] = wout1
            elif wout0 in ["vcpus", "memory_mb", "aggregates", "host_ip", "local_gb", "hypervisor_hostname"]:
                data[wout0] = wout1

        return data

    # Source the admin-openrc.sh file and capture the environment variables
    command = f"source {openrc_loc} && env"
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
    define_environmentals()

    env_vars = {}
    for line in proc.stdout:
        key, _, value = line.decode("utf-8").partition("=")
        env_vars[key] = value.strip()
    proc.communicate()

    print_data = {}

    if limit_computes and not get_all:
        hypervisor_indexes = compute_indexes
    else:
        hypervisor_indexes = get_host_list(env_vars)

    for i in hypervisor_indexes:
        print(i)

        details = get_host_details(i, env_vars)

        if details:
            print(details)
            print_data[details["hypervisor_hostname"]] = details

    return print_data


def get_virtual_machines():
    compute_service = conn.compute
    instances = compute_service.servers()
    return instances


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


def create_random_vms():

    floating_ips = get_floating_ips()
    allocated_ips = []

    network = conn.network.find_network(network_name)

    for i in range(20):

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
            server = conn.compute.create_server(name=name_mac, flavorRef=flavor.id, image_id=image_id,
                                                networks=[{"uuid": network.id}], adminPass=password)

        conn.compute.wait_for_server(server)
        # server.add_floating_ip_to_server(floating_ips[0])
        conn.compute.add_floating_ip_to_server(server, floating_ips[0])

        allocated_ips.append(floating_ips[0])

        floating_ips.pop(0)

        print(i)

    return allocated_ips


def get_all_vm_details():
    # Sanal makineler (örnekler) hakkýnda bilgi alýn
    def get_virtual_machines():
        compute_service = conn.compute
        instances = compute_service.servers()
        print(instances)
        return instances

    def get_vm_by_id(vm_id):

        compute_service = conn.compute
        try:
            vm = compute_service.get_server(vm_id)

            flav = vm.flavor.copy()

            if not use_zone:
                flav["host"] = vm.compute_host
            else:
                flav["host"] = vm.location["zone"]  # vm.zone
            # flav['compute_host'] = vm.compute_host
            asd = vm.addresses.copy()

            flav["ip"] = asd[network_name][ip_number]["addr"]

            return vm.name, flav

        except Exception as e:
            print(f"Error retrieving VM with ID {vm_id}: {e}")
            return None, None

    def get_flavors():

        data = {}
        virtual_machines = get_virtual_machines()

        for vm in virtual_machines:

            if not vm:
                continue

            print(vm)
            name, flavor = get_vm_by_id(vm.id)

            if not name:
                continue

            data[name] = str(vm)

        return {"result": data}

    return get_flavors()
