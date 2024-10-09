from typing import Literal

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


def shut_off_instance():
    api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="
    header = {"X-Auth-Key": api_key}
    resp = rq.get("http://10.150.1.30:5001/shutoff-instances", headers=header)
    return resp.json()


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
    # cur_vms = current_dist['virtual_machines'].to_list()
    cur_vms = current_dist['virtual_machines']
    nvm = random.randint(4, len(vm_list)) # Random number of VMs
    n_cur_vms = nvm // 4
    if n_cur_vms > len(cur_vms):
        n_cur_vms = len(cur_vms) // 4
    old_vms = random.sample(cur_vms, n_cur_vms)
    n_new_vms = nvm - n_cur_vms
    no_cur_vms = [vm for vm in vm_list if vm not in old_vms and vm.startswith('aypostest')]


    print(no_cur_vms, n_new_vms)

    new_vms = random.sample(no_cur_vms, n_new_vms)
    vms = old_vms + new_vms

    new_dist = {}

    # Loop over the range of random VMs
    for vm in vms:

        pm = random.choice(pms)
        # Assign the VM to the PM and update the current distribution
        current_dist[vm] = pm

    return current_dist


def get_random_distrubution(ip_addresses):
    node_exporter_data = process_req_now(ip_addresses['node_exporter_last_min'])
    pms_j = process_req_now(ip_addresses['pm_ip_address'])
    vms_j = process_req_now(ip_addresses['vm_ip_address'])
    snmp_j = process_req_now(ip_addresses['snmp_last_min'])
    print(node_exporter_data)
    pms = list(pms_j['res'].keys())
    pm_actual_names = {pms_j['res'][i]['host_ip']: pms_j['res'][i]['hypervisor_hostname'] for i in pms_j['res']}
    vm_actual_names = {vms_j['res'][i]['ip']: [i, vms_j['res'][i]['host']] for i in vms_j['res']}
    vms = list(vms_j['res'].keys())
    print(vm_actual_names)
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

    random_dist = random_distribution([vm[0] for vm in vm_actual_names.values()],
                                      list(pm_actual_names.values()),  # turn into list for random sample
                                      current_dist)
    print(random_dist)

    return random_dist


########################################################################################
def reformat_migration_json(some_migration_format) -> list[dict[str, str]]:

    del some_migration_format['virtual_machines']
    del some_migration_format['physical_machines']

    print(some_migration_format)

    migrate_dict = [{"vm_name": i, "to_host": some_migration_format[i]} for i in some_migration_format]

    """desired distribution format:
    [
    {"vm_name": "...", "to_pm": "..."},
    {"vm_name": "...", "to_pm": "..."},
    ...
    {"vm_name": "...", "to_pm": "..."},
    ]
    """

    return migrate_dict


def apply_distribution(distribution_list: list[dict[str, str]], migration_url="http://10.150.1.30:5001/migrate"):
    """desired distribution format:
    [
    {"vm_name": "...", "to_pm": "..."},
    {"vm_name": "...", "to_pm": "..."},
    ...
    {"vm_name": "...", "to_pm": "..."},
    ]

    """

    try:
        # won't iterate each one
        to = distribution_list[0]["to_host"]
        vm = distribution_list[0]["vm_name"]

    except Exception as e:
        raise e

    def migrate(migration_json, url="http://10.150.1.30:5001/migrate"):

        api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="

        header = {"X-Auth-Key": api_key}

        response = rq.post(url, json=str(migration_json), headers=header)
        # print(resp.text)
        # print(resp.status_code)
        try:
            response_json = response.json()
        except:
            response = rq.post(url, json=str(migration_json), headers=header)
            response_json = response.json()

        print(response_json)

        return response

    success = 0
    total = 0

    for i in distribution_list:

        response = migrate(i, migration_url)
        print(response.status_code)

        if response.status_code == 200:
            success += 1

        total += 1

    print("migration prop: ", success / total)

    return success/total

def culc_migration_advices():
    subprocess.Popen([
        'python',
        'C:\\Users\\B_L_C\\Desktop\\Real_Scenario_Data_Generator\\migration_advices.py'
    ])
    migration_advices_df = pd.read_csv('C:\\Users\\B_L_C\\Desktop\\Real_Scenario_Data_Generator\\migration_advices.csv')
    return migration_advices_df


def get_power(ip_addresses):

    snmp_j = process_req_now(ip_addresses['snmp_last_min'])

    snmps = {}

    print(snmp_j)

    for pm, snmp in snmp_j.items():
        print(pm)
        print(snmp)

        snmps[pm] = snmp['power']

    return {'snmp': snmps}

def get_ratio(first, second):

    differenc = first - second
    ratio = differenc / first
    return ratio

def culc_aypos_gain(ip_addresses, prop_gain_file_path = 'C:\\Users\\B_L_C\\Desktop\\Real_Scenario_Data_Generator\\gain_output.csv'):
    aypos_gain = {}
    data = get_power(ip_addresses)
    current_snmp = data['snmp']
    cur_total = pd.Series(current_snmp.values()).sum()
    prop_gain = pd.read_csv(prop_gain_file_path)
    prop_total = prop_gain['prop_total']
    past_total = prop_gain['cur_total']
    aypos_gain['prop_ratio'] = prop_gain['prop_gain']
    aypos_gain['actual_ratio'] = get_ratio(past_total, cur_total)
    aypos_gain['val_ratio'] = get_ratio(prop_total, cur_total)
    aypos_gain['val_difference'] = aypos_gain['prop_ratio'] - aypos_gain['actual_ratio']
    return aypos_gain





########################################################################################


ip_addresses = {
      "node_exporter_last_min":"http://10.150.1.167:8003/prom/aver/lastmin/1",
      "snmp_last_min":"http://10.150.1.167:8003/prom/snmp/n_min_aver_power/1",
      "pm_ip_address":"http://10.150.1.167:8003/prom/pm_mac_details",
      "vm_ip_address":"http://10.150.1.167:8003/prom/vm_mac_details",
       "migration_api_url": "http://10.150.1.30:5001/migrate"
}

random_dist = get_random_distrubution(ip_addresses)
desired_format = reformat_migration_json(random_dist)
apply_distribution(desired_format, ip_addresses["migration_api_url"])
#migration_advices_df = culc_migration_advices()
#desired_format = reformat_migration_json(migration_advices_df)
#apply_distribution(desired_format, ip_addresses["migration_api_url"])
#aypos_gain = culc_aypos_gain(ip_addresses)
#print(aypos_gain)
