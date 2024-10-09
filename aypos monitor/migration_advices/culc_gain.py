import pandas as pd
import random
import requests as rq
import numpy as np
import time
from datetime import datetime

from PIL.ImageChops import difference
from scipy.constants import value
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import pandas as pd
import copy, joblib, json, csv, os
import subprocess

# from migrationg_advices import migration_advices


# print(shut_off_instance())


##################################################################################################
# core functions
def process_req_now(ip):
    snmp_last_min = rq.get(ip).json()
    return snmp_last_min





def get_power(ip_addresses):

    snmp_j = process_req_now(ip_addresses['snmp_last_min'])

    snmps = {}

    print(snmp_j)

    for pm, snmp in snmp_j.items():
        print(pm)
        print(snmp)

        snmps[pm] = float(snmp['power'])

    return {'snmp': snmps}

def get_ratio(first, second):

    ratio = 1 - (first / second)
    return ratio

def culc_aypos_gain(ip_addresses, prop_gain_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\gain_output.csv',
                    open_computes=None):
    if open_computes is None:
        open_computes = ['compute3', 'compute4']

    aypos_gain = {}
    data = get_power(ip_addresses)
    current_snmp = data['snmp']

    do_once = True
    for comp in open_computes:
        if do_once:
            cur_power = current_snmp[comp]
            do_once = False
        else:
            cur_power += current_snmp[comp]

    # cur_power = current_snmp['compute4'] + current_snmp['compute3']  # compute1 and compute2 1!!!!!

    prop_gain = pd.read_csv(prop_gain_file_path)
    prop_power = prop_gain['prop_power'].iloc[0]
    past_power = prop_gain['cur_power'].iloc[0]
    aypos_gain['past_power'] = past_power
    aypos_gain['cur_power'] = cur_power
    aypos_gain['prop_power'] = prop_power
    aypos_gain['prop_ratio'] = prop_gain['prop_gain'].iloc[0]
    aypos_gain['actual_ratio'] = get_ratio(cur_power, past_power)
    aypos_gain['val_ratio'] = get_ratio(aypos_gain['actual_ratio'], aypos_gain['prop_ratio'])
    aypos_gain['val_difference'] = aypos_gain['prop_ratio'] - aypos_gain['actual_ratio']
    print(aypos_gain)
    aypos_gain = pd.DataFrame(data=list(aypos_gain.values()), index=list(aypos_gain.keys())).T
    return aypos_gain





ip_addresses = {
      "node_exporter_last_min":"http://10.150.1.167:8003/prom/aver/lastmin/1",
      "snmp_last_min":"http://10.150.1.167:8003/prom/snmp/n_min_aver_power/1",
      "pm_ip_address":"http://10.150.1.167:8003/prom/pm_mac_details",
      "vm_ip_address":"http://10.150.1.167:8003/prom/vm_mac_details",
       "migration_api_url": "http://10.150.1.30:5001/migrate"
}

# random_dist = get_random_distrubution(ip_addresses)
# desired_format = reformat_migration_json(random_dist)
# apply_distribution(desired_format, ip_addresses["migration_api_url"])
# ctrl + /    7 and shift
#migration_advices_df = culc_migration_advices()
#desired_format = reformat_migration_json(migration_advices_df)
#apply_distribution(desired_format, ip_addresses["migration_api_url"])


def runn_gain(computes_open=None):

    if computes_open is None:
        computes_open = ["compute3", "compute4"]

    aypos_gain = culc_aypos_gain(ip_addresses, open_computes=computes_open)

    aypos_dict = aypos_gain.to_dict()
    return aypos_dict


if __name__ == '__main__':
    runn_gain(4)
