import pandas
import requests
from .culc_gain import *
import ctypes  # An included library with Python install.


# class

# migrate function
def migrate(vm, host):
    api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="

    header = {"X-Auth-Key": api_key}
    mig_req = {"vm_name": vm, "to_host": host}

    resp = requests.post("http://10.150.1.30:5001/migrate", json=str(mig_req), headers=header)
    # print(resp.text)
    print(resp.status_code)
    print(resp.json())
    return resp.status_code, resp.json()


def gain_pop_up(gain_result):
    ctypes.windll.user32.MessageBoxW(0, str(gain_result), "Gain Result", 1)


# use this function and give a dataframe in usual format
def req_migrate_one_by_one(df_migration_advices: pandas.DataFrame):
    list_computes = df_migration_advices[df_migration_advices["vm"]=='Acik']['pm'].tolist()
    y_data:dict = eval(df_migration_advices.to_json())
    print(y_data)

    # Create a dictionary to store the desired output
    mig_dict = {}
    open_computes = []

    # Iterate over the keys and values in the "vm" and "pm" dictionaries
    for vm_id, vm_status in y_data["vm"].items():
        pm_name = y_data["pm"][vm_id]
        if vm_status == 'Kapali' or vm_status == 'Acik':

            continue

        mig_dict[vm_status] = pm_name

    ct = 0
    allc = len(mig_dict.keys())

    hosts = []
    # run migration
    for key in mig_dict:
        vm = key
        host = mig_dict[key]
        if host not in hosts:
            hosts.append(host)

        # migrate here
        stat, response = migrate(vm, host)
        if stat == 200:
            ct += 1
        elif stat==500:
            resp_text = response['response']
            print(resp_text)

            if 'current host' in resp_text:
                print("increasing ct, current host migration try")
                ct += 1

    success = ct/allc
    print(success)
    gain_result: dict = runn_gain(list_computes)
    # is this fine?
    # show gain when the threat migration enforcement is over
    # may be it can run gain function give gain output this is much more easier
    pandas.DataFrame(gain_result).to_csv('C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\gain_output.csv')
    gain_pop_up(gain_result)


if __name__=='__main__':
    # df = pandas.DataFrame(...)
    # req_migrate_one_by_one(df)
    df = pandas.read_csv("C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\migration_advices.csv")
    df = df.iloc[:, 1:]
    print(df.columns)
    print(df[df["vm"]=='Acik'])
    req_migrate_one_by_one(df)
    pass
