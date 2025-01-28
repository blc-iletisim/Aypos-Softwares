'''
    server = conn.compute.get_server(server_id)
    conn.compute.wait_for_server(server)
    addrs = server.addresses['Internal'][1]['addr']

'''

# steps,
# 1 - configure openstack_configs.py using you openstack-rc file
# 2 - run create flavors python file and create random flavors.
# 2 - ...

#### Configure Below Before Starting ####

# write here config file location
openrc_loc = "/home/ubuntu/admin-openrc.sh"

# example openstack server object below, use addresses to configure you will see similar after running configs.py on controller
"""openstack.compute.v2.server.Server(id=2e89fdc9-d79c-4b07-baa7-e49391822c7d, name=blc-cloud, "
 "status=SHUTOFF, tenant_id=48966d34ff274def88db7f7b6d9f5cdc, user_id=4a115b66d4bf43fabd51fac4331c311e, "
 "metadata={}, hostId=c275e4a48285b38bd3448a85e2bc3dc20bd3c6ddb97187937a4db0c1, "
 "image={'id': '20944105-1877-4935-bacd-d68dc3691ade', "
 "'links': [{'rel': 'bookmark', 'href': 'http://10.150.1.251:8774/images/20944105-1877-4935-bacd-d68dc3691ade'}]}, "
 "flavor={'vcpus': 8, 'ram': 16384, 'disk': 160, 'ephemeral': 0, 'swap': 0, 'original_name': 'm1.xlarge', "
 "'extra_specs': {}}, created=2022-08-19T12:48:39Z, updated=2025-01-26T14:17:26Z, "
 "addresses={'Internal': [{'version': 4, 'addr': '10.10.10.144', 'OS-EXT-IPS:type': 'fixed', "
 "'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:d1:c4:da'}, {'version': 4, 'addr': '10.150.1.150', 'OS-EXT-IPS:type': 'floating', "
 "'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:d1:c4:da'}]}, accessIPv4=, accessIPv6=, "
 "links=[{'rel': 'self', 'href': 'http://10.150.1.251:8774/v2.1/servers/2e89fdc9-d79c-4b07-baa7-e49391822c7d'}, "
 "{'rel': 'bookmark', 'href': 'http://10.150.1.251:8774/servers/2e89fdc9-d79c-4b07-baa7-e49391822c7d'}], "
 "OS-DCF:diskConfig=MANUAL, OS-EXT-AZ:availability_zone=nova, config_drive=, key_name=aybuke-netgsmkey, "
 "OS-SRV-USG:launched_at=2022-09-14T06:01:48.000000, OS-SRV-USG:terminated_at=None, "
 "OS-EXT-SRV-ATTR:host=compute1, OS-EXT-SRV-ATTR:instance_name=instance-0000010d, "
 "OS-EXT-SRV-ATTR:hypervisor_hostname=compute1, OS-EXT-SRV-ATTR:reservation_id=r-5ul69ijn, "
 "OS-EXT-SRV-ATTR:launch_index=0, OS-EXT-SRV-ATTR:hostname=blc-cloud, OS-EXT-SRV-ATTR:kernel_id=, "
 "OS-EXT-SRV-ATTR:ramdisk_id=, OS-EXT-SRV-ATTR:root_device_name=/dev/vda, OS-EXT-SRV-ATTR:user_data=None, "
 "OS-EXT-STS:task_state=None, OS-EXT-STS:vm_state=stopped, OS-EXT-STS:power_state=0, "
 "os-extended-volumes:volumes_attached=[{'id': '472e8f3c-5201-4464-a666-7fb1b871d470', 'delete_on_termination': False}], "
 "locked=True, description=None, tags=[], trusted_image_certificates=None, host_status=UP, "
 "security_groups=[{'name': 'allow_all'}, {'name': 'default'}], location=Munch({'cloud': 'defaults', 'region_name': '', "
 "'zone': 'nova', 'project': Munch({'id': '48966d34ff274def88db7f7b6d9f5cdc', 'name': 'admin', "
 "'domain_id': None, 'domain_name': 'Default'})}))"""

# configure ones below. Run me on controller, $ python3 configs.py
network_name = "Internal"  # configure me !! using 
ip_number = 1  # configure me  !!
use_zone = False  # if host is empty or nan, change me to True

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
