
import pandas as pd
import random
import requests as rq
import numpy as np
import time
from datetime import datetime

from PIL.ImageChops import difference
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import pandas as pd
import copy, joblib, json, csv, os
import subprocess

from migrationg_advices import migration_advices




# print(shut_off_instance())


##################################################################################################
# core functions
def process_req_now(ip):
    snmp_last_min = rq.get(ip).json()
    return snmp_last_min


def random_distribution(vm_list, pm_list, current_dist):
    # Generate random numbers less than the lengths of vm_list and pm_list
    npm = random.randint(2, len(pm_list))  # Random number of PMs
    pms = random.sample(pm_list, npm)
    no_cur_vms = [vm for vm in vm_list if vm.startswith('aypos_tester')]
    nvm = random.randint(4, len(no_cur_vms)) # Random number of VMs

    n_new_vms = nvm





    new_vms = random.sample(no_cur_vms, n_new_vms)
    vms = new_vms

    new_dist = {}

    # Loop over the range of random VMs
    for vm in vms:

        pm = random.choice(pms)
        # Assign the VM to the PM and update the current distribution
        new_dist[vm] = pm

    return new_dist


def get_random_distrubution(ip_addresses):
    node_exporter_data = process_req_now(ip_addresses['node_exporter_last_min'])
    pms_j = process_req_now(ip_addresses['pm_ip_address'])
    vms_j = process_req_now(ip_addresses['vm_ip_address'])
    snmp_j = process_req_now(ip_addresses['snmp_last_min'])
    print(pms_j, vms_j)
    pms = list(pms_j['res'].keys())
    pm_actual_names = {pms_j['res'][i]['host_ip']: pms_j['res'][i]['hypervisor_hostname'] for i in pms_j['res']}
    vm_actual_names = {vms_j['res'][i]['ip']: [i, vms_j['res'][i]['host']] for i in vms_j['res']}
    vms = list(vms_j['res'].keys())

    virtual_machines = []
    physical_machines = []

    # print(vms)
    # print(node_exporter_data.keys())

    for i, _ in node_exporter_data.items():

        if i in list(vm_actual_names.keys()):
            # print(i)
            # print(i)
            # physical_machines[pm_aggregate[i]] = node_exporter_data[i]
            pm_name = vm_actual_names[i][1]
            vm_name = vm_actual_names[i][0]
            physical_machines.append(pm_name)
            virtual_machines.append(vm_name)

    # wth casting df
    # current_dist = pd.DataFrame({'virtual_machines': virtual_machines, 'physical_machines': physical_machines})
    current_dist = {'virtual_machines': virtual_machines, 'physical_machines': physical_machines}
    print(current_dist)

    random_dist = random_distribution([vm[0] for vm in vm_actual_names.values()],
                                      list(pm_actual_names.values()),  # turn into list for random sample
                                      current_dist)
    print(random_dist)

    return random_dist


ip_addresses = {
      "node_exporter_last_min":"http://10.150.1.167:8003/prom/aver/lastmin/1",
      "snmp_last_min":"http://10.150.1.167:8003/prom/snmp/n_min_aver_power/1",
      "pm_ip_address":"http://10.150.1.167:8003/prom/pm_mac_details",
      "vm_ip_address":"http://10.150.1.167:8003/prom/vm_mac_details",
       "migration_api_url": "http://10.150.1.30:5001/migrate"
}


dist = get_random_distrubution(ip_addresses)
print(type(dist))
