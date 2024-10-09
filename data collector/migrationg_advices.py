import pandas as pd
import random
import requests as rq
import numpy as np
import time
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import pandas as pd
import copy
import joblib
import json
import csv
import os
import sys
import json
from multiprocessing import Queue
import os


##################################################################################################
# core functions
def process_req_now(ip):
    snmp_last_min = rq.get(ip).json()
    return snmp_last_min


def get_p_req_cur(ip_addresses):
    node_exporter_data = process_req_now(ip_addresses['node_exporter_last_min'])
    pms_j = process_req_now(ip_addresses['pm_ip_address'])
    vms_j = process_req_now(ip_addresses['vm_ip_address'])
    snmp_j = process_req_now(ip_addresses['snmp_last_min'])

    pms = list(pms_j['res'].keys())
    pm_actual_names = {pms_j['res'][i]['host_ip']: pms_j['res'][i]['hypervisor_hostname'] for i in pms_j['res']}
    vm_actual_names = {vms_j['res'][i]['ip']: [i, vms_j['res'][i]['host']] for i in vms_j['res']}
    vms = list(vms_j['res'].keys())

    virtual_machines = {}
    physical_machines = {}

    # print(vms)
    # print(node_exporter_data.keys())

    for i, _ in node_exporter_data.items():

        if i in list(pm_actual_names.keys()):
            # print(i)
            # physical_machines[pm_aggregate[i]] = node_exporter_data[i]
            pm_name = pm_actual_names[i]
            snmp = snmp_j[pm_name].copy()
            snmp_df = pd.DataFrame(data=list(snmp.values()), index=list(snmp.keys())).T
            pm = node_exporter_data[i]
            pm_df = pd.DataFrame(data=list(pm.values()), index=list(pm.keys())).T
            physical_machines[pm_name] = pd.concat([pm_df, snmp_df], axis=1)

        if i in list(vm_actual_names.keys()):
            # print(i)
            # print(i)
            # physical_machines[pm_aggregate[i]] = node_exporter_data[i]
            pm_name = vm_actual_names[i][1]
            name = vm_actual_names[i][0]
            snmp = snmp_j[pm_name].copy()
            snmp_df = pd.DataFrame(data=list(snmp.values()), index=list(snmp.keys())).T
            vm = node_exporter_data[i]
            vm_df = pd.DataFrame(data=list(vm.values()), index=list(vm.keys())).T
            virtual_machines[name] = pd.concat([vm_df, snmp_df], axis=1)

    snmps = {}

    print(snmp_j)

    for pm, snmp in snmp_j.items():
        print(pm)
        print(snmp)

        snmps[pm] = snmp['power']

    return {'physical_machines': physical_machines, 'virtual_machines': virtual_machines, 'snmp': snmps}


def initialize_confg_data(pm_ip_address, vm_ip_address):
    pms_j = process_req_now(pm_ip_address)
    vms_j = process_req_now(vm_ip_address)
    print(pms_j, vms_j)

    physical_machines = [
        [pms_j['res'][pm]['hypervisor_hostname'], int(pms_j['res'][pm]['vcpus']), int(pms_j['res'][pm]['memory_mb']),
         int(pms_j['res'][pm]['local_gb']), int(pms_j['res'][pm]['idle consumption'])] for pm in pms_j['res']]

    virtual_machines = {
        vm: [vm, int(vms_j['res'][vm]['vcpus']), int(vms_j['res'][vm]['ram']), int(vms_j['res'][vm]['disk'])] for vm in
        vms_j['res']}

    return {'physical_machines': physical_machines, 'virtual_machines': virtual_machines}


def culc_idle_p(actual_df):
    sort_power = actual_df["power"].unique()
    sort_power.sort()
    idle_p = sort_power[(random.randint(40, 60)) * 10]

    return idle_p


def feature_extraction(data, actual_df, scaler, cols):
    pm_data = data['physical_machines']

    vm_data = data['virtual_machines']

    idle_p = culc_idle_p(actual_df)

    power = []
    print(pm_data)
    for pm_name, pm in pm_data.items():
        power.append(float(pm_data[pm_name]['power'].to_numpy()[0]) - float(idle_p))

    power = np.mean(power)

    # vm3_data.insert(54, 'Sockstat UDP Inuse', 0)
    features = {}

    for vm_name, vm in vm_data.items():
        df_vm = vm[cols]
        df_vm_s = scaler.transform(df_vm)
        features[vm_name] = df_vm_s

    features['power'] = power

    return features


def predict_vm_power(model, features):
    power = features.pop('power')
    predictions = {}

    for feature_name, feature in features.items():

        prediction = model.predict(xgb.DMatrix(feature))

        if (prediction[0] > 0.09):
            prediction = prediction[0]
        else:
            prediction = 0

        predictions[feature_name] = prediction

    for prediction_name, prediction in predictions.items():
        predictions[prediction_name] = (prediction / (sum(predictions.values()) + 0.000001)) * power

    return predictions


def add_vm_p_to_confg(actual_data, vm_power):
    data = copy.deepcopy(actual_data)

    vm_confg = []

    for vm_name, power in vm_power.items():
        data['virtual_machines'][vm_name].append(int(vm_power[vm_name]))
        vm_confg.append(data['virtual_machines'][vm_name])

    data['virtual_machines'] = vm_confg

    return data


def migration_advices(data, vm_power):
    confg = add_vm_p_to_confg(data, vm_power)

    fiziksel_makineler = confg['physical_machines']
    sanal_makineler = confg['virtual_machines']

    # Karar değişkenleri
    x = LpVariable.dicts("x", ((i, j) for i in range(len(fiziksel_makineler)) for j in range(len(sanal_makineler))),
                         cat="Binary")
    y = LpVariable.dicts("y", range(len(fiziksel_makineler)), cat="Binary")

    # Lineer Programlama modeli oluşturma
    model = LpProblem(name="SanalMakineYerlestirme", sense=LpMinimize)

    # Hedef fonksiyonu tanımlama
    model += lpSum(y[i] * fiziksel_makineler[i][4] for i in range(len(fiziksel_makineler))) + lpSum(
        x[i, j] * sanal_makineler[j][4] for i in range(len(fiziksel_makineler)) for j in range(len(sanal_makineler)))

    # Kısıtlar

    # Her sanal makine bir fiziksel makineye atanmalı
    for j in range(len(sanal_makineler)):
        model += lpSum(x[i, j] for i in range(len(fiziksel_makineler))) == 1

    # Fiziksel makinelerin kapasite kısıtları
    for i in range(len(fiziksel_makineler)):
        model += lpSum(x[i, j] * sanal_makineler[j][1] for j in range(len(sanal_makineler))) <= fiziksel_makineler[i][
            1] * y[i]
        model += lpSum(x[i, j] * sanal_makineler[j][2] for j in range(len(sanal_makineler))) <= fiziksel_makineler[i][
            2] * y[i]
        model += lpSum(x[i, j] * sanal_makineler[j][3] for j in range(len(sanal_makineler))) <= fiziksel_makineler[i][
            3] * y[i]

    # Fiziksel makinelerin kullanılabilirlik kısıtları
    for i in range(len(fiziksel_makineler)):
        model += lpSum(x[i, j] for j in range(len(sanal_makineler))) <= 1000 * y[i]

    # Modeli çözme
    model.solve()

    # Sonuçları DataFrame'e ekleme
    results = {"vm": [], "pm": [], "GucTuketimi": []}

    for i, fiziksel_makine in enumerate(fiziksel_makineler):
        results["pm"].append(fiziksel_makineler[i][0])
        results["vm"].append("Acik" if y[i].varValue == 1 else "Kapali")
        if y[i].varValue == 1:
            toplam_tuketim = fiziksel_makineler[i][4] + lpSum(
                x[i, j].varValue * sanal_makineler[j][4] for j in range(len(sanal_makineler)))
            results["GucTuketimi"].append(toplam_tuketim.value())
        else:
            results["GucTuketimi"].append(0)

    # Sanal makinelerin atanma durumu
    for j, sanal_makine in enumerate(sanal_makineler):
        for i in range(len(fiziksel_makineler)):
            if x[i, j].varValue == 1:
                results["pm"].append(fiziksel_makineler[i][0])
                results["vm"].append(sanal_makine[0])
                results["GucTuketimi"].append(sanal_makine[4])

    # DataFrame oluşturma
    df_results = pd.DataFrame(results)

    return df_results


def gain_function(df_results, data, confg):
    pm_confg = confg['physical_machines']
    print(pm_confg)
    print('*******************you entered this finction*****************')
    current_snmp = data['snmp']
    print('*******************you entered this finction*****************')
    print(current_snmp, type(np.array(current_snmp.values())))
    power = pd.Series(current_snmp.values()).sum()
    print(power)
    print('*******************you entered this finction*****************')
    max_df = df_results[df_results['vm'] == 'Acik']
    df_not = df_results[df_results['vm'] == 'Kapali']
    ic = 0
    for pm in df_not['pm'].tolist():
        print(pm, type(pm))
        for cpm in pm_confg:
            print(cpm, type(cpm))
            if cpm[0] == pm:
                ic = ic + int(cpm[-1])

    power1 = power - ic
    print('*******************you entered this finction*****************')
    print('1', max_df['GucTuketimi'].sum(), '2', type(power), power)
    ratio = 1 - (float(max_df['GucTuketimi'].sum()) / float(power))
    print(ratio)
    max_df['prop_gain'] = ratio
    max_df['prop_power'] = float(max_df['GucTuketimi'].sum())
    max_df['cur_power'] = power

    max_df = max_df[['prop_gain', 'prop_power', 'cur_power']]

    return max_df


##################################################################################################
# one time calling functions

def script_initializer(user_inputs):
    congf_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\script_config.json'

    # Open the JSON file
    with open(congf_file_path, 'r') as file:
        # Load the JSON data
        script_confg = json.load(file)

    script_time_unit = int(user_inputs['script_time_unit'])
    p_ip_addresses = script_confg['ip_addresses']['get_ip_addresses']
    pm_ip_address = script_confg['ip_addresses']['get_ip_addresses']['pm_ip_address']
    vm_ip_address = script_confg['ip_addresses']['get_ip_addresses']['vm_ip_address']
    print(pm_ip_address, vm_ip_address)
    data = initialize_confg_data(pm_ip_address, vm_ip_address)
    actual_df_file_path = script_confg['actual_df']
    actual_df = pd.read_csv(actual_df_file_path)
    columns_file_path = script_confg['models'][user_inputs['model_type']]['columns']
    energy_after_corr_columns = pd.read_csv(columns_file_path)
    print(energy_after_corr_columns['0'])
    cols = energy_after_corr_columns['0'].tolist()
    scaler_file_path = script_confg['models'][user_inputs['model_type']]['scaler']
    scaler = joblib.load(scaler_file_path)
    model_file_path = script_confg['models'][user_inputs['model_type']]['model']
    print(model_file_path)
    model = xgb.Booster()
    model.load_model(model_file_path)
    api_url = script_confg['ip_addresses']['post_ip_addresses']['api_url']
    api_prime_url = script_confg['ip_addresses']['post_ip_addresses']['api_prime_url']

    parameters = (
        script_time_unit, p_ip_addresses, data, actual_df, cols, scaler, model, api_url, api_prime_url
    )

    return parameters


def script_finalizer(initial_rows_file_path, model_file_path, updated_data, len_start_data, model):
    model.save(model_file_path)
    updated_data = updated_data.to_frame()
    headers = updated_data.columns

    with open(initial_rows_file_path, 'a', newline='') as file:
        writer = csv.writer(file)

        # If the file does not exist, write the header
        if not initial_rows_file_path:
            writer.writerow(headers)

        # Write new rows
        writer.writerows(updated_data.iloc[len_start_data:]['power'].to_list())


##################################################################################################
# CPT functions

def connect(connection_condition):
    return get_p_req_cur(connection_condition)


def process(connection, data, actual_df, scaler, cols, model, script_time_unit):
    features = feature_extraction(connection, actual_df, scaler, cols)
    vm_power = predict_vm_power(model, features)
    df_migration_advices = migration_advices(data, vm_power)
    gain = gain_function(df_migration_advices, connection, data)

    data = eval(df_migration_advices.to_json())

    la = {"pms": {}}
    ma = {"runningPms": [], "offPms": []}

    for i in data["vm"]:

        if data["vm"][i] == "Kapali":
            ma["offPms"].append(data["pm"][i])
            continue

        if data["vm"][i] == "Acik":
            ma["runningPms"].append(data["pm"][i])
            continue

        if data["pm"][i] in la["pms"].keys():
            la["pms"][data["pm"][i]]["vms"].append(data["vm"][i])
            la["pms"][data["pm"][i]]["vmpower"].append(data["GucTuketimi"][i])
        else:
            la["pms"][data["pm"][i]] = {"vms": [], "vmpower": []}
            la["pms"][data["pm"][i]]["vms"].append(data["vm"][i])
            la["pms"][data["pm"][i]]["vmpower"].append(data["GucTuketimi"][i])

    return ma, la, gain, df_migration_advices


def transact(a_process, api_url):
    return rq.post(api_url, json=a_process)


##################################################################################################
# defining constants and doing one time processes
def write_to_csv(value, file_path):
    # Check if the file exists

    # Open the file in append mode
    value.to_csv(file_path)


def delete_file_if_exists(file_path='C:\\Users\\B_L_C\\Desktop\\Real_Scenario_Data_Generator\\migration_advices.csv'):
    if os.path.isfile(file_path):
        os.remove(file_path)


file_path = 'C:\\Users\\B_L_C\\Desktop\\Real_Scenario_Data_Generator\\gain_output.csv'


def main(user_inputs):
    # Send data to the FastAPI app every 1 minute

    parameters = script_initializer(user_inputs)
    script_time_unit, p_ip_addresses, data, actual_df, cols, scaler, model, api_url, api_prime_url = parameters
    # {data: key1: [...data...], ...}
    # Send data to the FastAPI app every 20 minutes

    connection = connect(p_ip_addresses)
    prime_mig_data, mig_chart_data, gain, df_migration_advices = process(connection, data, actual_df, scaler, cols,
                                                                         model, script_time_unit)
    temp_a_process = df_migration_advices
    write_to_csv(df_migration_advices, 'C:\\Users\\B_L_C\\Desktop\\Real_Scenario_Data_Generator\\migration_advices.csv')
    write_to_csv(gain, file_path)
    # gain_data = gain.to_json()["ratio"]["1"]
    # ...

    #  mig_chart_data["ratio"] = gain_data
    # print('#########################', mig_chart_data)
    # print('################', prime_mig_data)
    print(gain, '##########################')
    print('##############', df_migration_advices)
    y_data = eval(df_migration_advices.to_json())

    # Create a dictionary to store the desired output
    result = {}

    # Iterate over the keys and values in the "vm" and "pm" dictionaries
    for vm_id, vm_status in y_data["vm"].items():
        pm_name = y_data["pm"][vm_id]
        if vm_status == 'Kapali' or vm_status == 'Acik':
            continue

        result[vm_status] = pm_name

    # Print the resulting dictionary
    print(result)
    return (result, {'y':df_migration_advices, 'x':data})
    '''mig_chart_data['pms']["compute2"]["vms"].append("keycloCK")
    mig_chart_data['pms']["compute2"]["vmpower"].append(120.4)

    mig_chart_data['pms']["compute2"]["vms"].append("blc-meet")
    mig_chart_data['pms']["compute2"]["vmpower"].append(130.8)

    response = transact(mig_chart_data, api_url)

    response_2 = transact(prime_mig_data, api_prime_url)
    print(mig_chart_data)

    print("Response from API:", response_2.json())
    print('')'''

    time.sleep(script_time_unit)  # sleep for 20 mins


if __name__ == "__main__":
    # user_inputs = json.loads(sys.argv[1])
    user_inputs = {
        'script_time_unit': '20',
        'model_type': 'xgboost'
    }

    # Run the main function
    main(user_inputs)
