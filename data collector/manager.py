import time

import requests
from migrationg_advices import *
from start_stress import *

from culc_aypos_gain import *
from DataHandler import *
from data_saver import *

controller_api = "http://10.150.1.30:5001"
ansible_api = "http://172.18.15.79:8000"


# time.sleep(90*60)
def create_dist_vms(num):
    res = requests.get(f"{controller_api}/create-vms/{num}")
    return res.status_code


def delete_vms(num):
    res = requests.get(f"{controller_api}/delete-vms/{num}")
    return res.status_code


def remove_known_hosts():
    res = requests.get(f"{ansible_api}/remove_known")
    return res.status_code


def start_ansible(num):
    res = requests.get(f"{ansible_api}/start_ansible/{num}")
    return res.status_code


# when there is a problem it saves last step
# it sends email and stop
# if migration not applied 100 percent:
# 1 overwrite the value of total_count with the recent vlue of i
# 2 send an email and want to be fixed manually nth iteration


def migrate(vm, host):
    api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="

    header = {"X-Auth-Key": api_key}
    mig_req = {"vm_name": vm, "to_host": host}

    resp = requests.post("{controller_api}/migrate", json=str(mig_req), headers=header)
    # print(resp.text)
    print(resp.status_code)
    print(resp.json())
    return resp.status_code, resp.json()


def format_jsons(gain_dict: dict):
    formatted_dict = {}

    for key, value in gain_dict.items():
        float_val = value.get("0")
        print("key: ", key)
        print("value: ", value)
        float_val = value[0]

        formatted_dict[key] = float_val

    return formatted_dict


def handle_migrations(mig_dict):

    ct = 0
    allc = len(mig_dict.keys())

    last_step = ""
    hosts = []
    # run migration
    for key in mig_dict:
        vm = key
        host = mig_dict[key]
        last_step = str(vm) + str(host)
        if host not in hosts:
            hosts.append(host)

        stat, response = migrate(vm, host)
        if stat == 200:
            ct += 1
        elif stat==500:
            resp_text = response['response']
            print(resp_text)

            if 'current host' in resp_text:
                print("increasing ct, current host migration try")
                ct += 1

    return ct/allc, last_step, hosts


# create_dist_vms()
# delete_vms()
# exit()
def write_into_savef(num, data):
    name = "save_mig" + str(num)
    with open(name, "w") as f:
        f.write(json.dumps(data))

start = 200
# regression data and logs will be saved into database
############################################################################
Mohamed_email = "mohamedalbyoumi@gmail.com"  # your email here Mohamed   <-------------------------
# it already sends me email too but i don't see emails sometimes it will send us both
dh = DatabaseHandler(Mohamed_email)

last_data = dh.get_last_data()  # dont change
last_step = last_data[1]   # dont change
is_success = last_data[2]  # dont change

# here you can change variables Mohamed
total_count = 1020

max_machine = 10
min_machine = 5  # may be 4 idk

# !!! you can machine_num = random.randint(min_machine, max_machine) in loop below
# but AT THE END of the loop or AT START of it

machine_num = 7  # total number of machines created and migrated...
success_min = 0.8
repeating_error_max = 5
repeating_error = 0

############################################################################
while True:
    try:
        # start = time.time()
        if repeating_error > repeating_error_max:
            dh.send_email("sed3718@gmail.com", "quitted from main loop error num is 6")
            dh.save_log_to_db()
            break

        for i in range(total_count):

            start = time.time()
            ## i is not used
            ## you can let the line below run here
            # random machine number
            machine_num = random.randint(min_machine, max_machine)

            last_data = dh.get_last_data()  # dont change
            last_step = last_data[1]  # dont change
            is_success = last_data[2]  # dont change

            ## make sure of getting last step
            if is_success:
                cur_step = int(last_step) + 1
            else:
                cur_step = int(last_step)

            ## end it when total data is collected
            print("[*] Types cur_step, total_count: ", type(cur_step), type(total_count), cur_step, total_count)

            if int(cur_step) > int(total_count):
                print(f"{total_count} data collected successfully")
                break

            print(cur_step)

            dh.shape_log_step(step=cur_step)

            save_num = start + cur_step

            dh.shape_log_text(last_log="[*] VMs being created")

            try:
                create_dist_vms(machine_num)
                dh.shape_log_text(last_log="[*] VMs created")
                print("[*] VMs created")
            except Exception as e:
                print(e)
                dh.shape_log_success(is_success=False)
                dh.save_log_to_db()
                delete_vms(machine_num)
                repeating_error += 1
                break

            dh.shape_log_text(last_log="[*] Known hosts being removed")

            try:
                remove_known_hosts()
                print("[*] Known hosts removed")
            except Exception as e:
                print(e)
                dh.shape_log_success(is_success=False)
                dh.save_log_to_db()
                delete_vms(machine_num)
                repeating_error += 1
                break

            # time.sleep(10)
            """dh.shape_log_text(last_log="[*] Ansible being started")
            try:
                start_ansible(machine_num)
                print("[*] Ansible started")
            except:
                dh.shape_log_success(is_success=False)
                dh.save_log_to_db()
                delete_vms(machine_num)
                repeating_error += 1
                break"""

            # exit()
            time.sleep(15)
            dh.shape_log_text(last_log="[*] Stresses starting")
            try:
                start_stress_es(machine_num)
                print("[*] Stress started")
            except Exception as e:
                print(e)

                dh.shape_log_success(is_success=False)
                dh.save_log_to_db()
                delete_vms(machine_num)
                repeating_error += 1
                break

            # user_inputs = json.loads(sys.argv[1])
            user_inputs = {
                'script_time_unit': '20',
                'model_type': 'xgboost'
            }

            time.sleep(20)

            dh.shape_log_text(last_log="[*] Migrations starting")
            try:
                migrations, training_data = main(user_inputs)
                save_training_data(training_data['y'], training_data['x'])
                print("[*] Migrations received, ", migrations)

                success_num, last_step, computes = handle_migrations(migrations)
                print("[*] Success: ", success_num)

                if success_num < success_min:

                    dh.shape_log_success(is_success=False)
                    dh.shape_log_text('migration is not applied well. Removing vms and trying new step. Migration proportion: ' + str(success_num))
                    dh.save_log_to_db()

                    print("migrations: ", migrations)
                    print("last step: ", last_step)
                    repeating_error += 1

                    # wait_till = input("[*] Please migrate and enter: ")
                    delete_vms(machine_num)
                    break
                else:
                    print("[*] Migration done well. ")
            except Exception as e:
                print("[*] Migration error: ", e)
                dh.shape_log_success(is_success=False)
                dh.save_log_to_db()
                delete_vms(machine_num)
                repeating_error += 1
                break

            time.sleep(23)

            dh.shape_log_text(last_log="[*] Gain and write starting")
            try:
                write_into_savef(save_num, migrations)
                print("writter")
                gain_dict = runn_gain(save_num, computes)
                print(gain_dict)

                formatted_gain = format_jsons(gain_dict)
                print(formatted_gain)

                # past_power, cur_power, prop_power, prop_ratio, actual_ratio, val_ratio, val_difference
                dh.save_regs_to_db(past_power=formatted_gain["past_power"], cur_power=formatted_gain["cur_power"],
                                   prop_power=formatted_gain["prop_power"], prop_ratio=formatted_gain["prop_ratio"]
                                   ,actual_ratio=formatted_gain["actual_ratio"] ,val_ratio=formatted_gain["val_ratio"],
                                   val_difference=formatted_gain["val_difference"])

                print("[*] Gain ran")

            except Exception as e:
                print("exception: ", e)
                dh.shape_log_success(is_success=False)

                dh.save_log_to_db()
                repeating_error += 1
                break

            dh.shape_log_text(last_log="[*] delete vms")
            try:
                delete_vms(machine_num)
                print("[*] VMs deleted")
            except:
                dh.shape_log_success(is_success=False)
                dh.save_log_to_db()
                repeating_error += 1
                break

            dh.save_log_to_db()
            repeating_error = 0
            end = time.time()
            print("[*] Time took: ", end - start)
            time.sleep(15)

        else:
            delete_vms(machine_num)
            print("[*] Error, VMs deleted")

    except:
        ...
