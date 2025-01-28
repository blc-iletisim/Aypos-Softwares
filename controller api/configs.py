'''
    server = conn.compute.get_server(server_id)
    conn.compute.wait_for_server(server)
    addrs = server.addresses['Internal'][1]['addr']

'''

# steps,
# 1 - run create flavors python file and create random flavors.
# 2 - ...

#### Configure Below Before Starting ####

# write here config file location
openrc_loc = "/home/ubuntu/admin-openrc.sh"

# configure ones below. Run me on controller, $ python3 configs.py
network_name = "Internal"  # configure me !!
ip_number = 1  # configure me  !!
use_zone = False  # run me if host is empty change me to True

prometheus_vm_openstack_name = 'prometheus_serverV3'  # better change this for reliability but optional

#### Optional Variables ####
# if you want to limit computes for getting pm conf with using  | optional
limit_computes = False  # if you make true change indexes below
compute_indexes = [54, 57]  # get indexes using: $ openstack hypervisor list

use_pem = False
pem_file_name = ""  # if use pem false don't configure me
password = "blc123"

## DATA COLLECTOR VARS
# image id for creating random vms !! change below
image_id = "20944105-1877-4935-bacd-d68dc3691ade"  # image which already installed node exporter and stress tools on it and stress script


### API VARS
# api configs are ok don't need to change
flask_port = 5001
flask_host = '0.0.0.0'


# below for connection object and helping with configurations
from openstack_configs import *
from openstack import connection
import random


API_KEY = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="

# OpenStack ortamýna baðlantý oluþturun
conn = connection.Connection(
    auth_url=auth_url,
    project_name=project_name,
    username=username,
    password=password,
    user_domain_name=user_domain_name,
    project_domain_name=project_domain_name,
    )


if __name__=='__main__':
    # run this python script for configuring network_name and ip_number above

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

    print(get_flavors())
