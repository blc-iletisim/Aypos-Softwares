from fastapi import FastAPI, Depends
import re
from handler_funcs import *
# from decimal import Decimal
from database import *
from fastapi.responses import FileResponse, JSONResponse
import os
import subprocess
# from fastapi.responses import JSONResponse
# import paramiko
import psutil
from fabric import Connection
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
from informative_scripts import *
import requests as rq


app = FastAPI()
origins = ["*"]

message_ew = {'messages': [{'message': 'Current power utilization :420.5 Watt <br>Proposed power utilization: 405.3<br>Expected power gain: %3.58', 'show': 1, 'message_id': 1}]}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Queue:

    def __init__(self, file_name):
        self.queue = []
        self.max_amount = 100
        self.length = 0
        self.file_name = file_name
        self.save_ct = 0
        
        try:
            ofile = open(self.file_name, 'r')
            self.queue = eval(ofile.read())
            ofile.close()

        except Exception as e:
            print("error at reading file ", self.file_name)
            print(e)
            ofile = open(self.file_name, 'w')
            ofile.write(str(self.queue))
            ofile.close()
    
    def push(self, data):

        if len(self.queue) > self.max_amount:
            self.queue.pop(0)
            self.queue.append(data)

            #while len(self.queue) > self.max_amount:
            #    self.queue.pop(0)

            self.length = len(self.queue)

        else:
            print("sec")
            self.queue.append(data)
            self.length = len(self.queue)
        
        if self.save_ct > 5:
            self.save_ct = 0
            try:

                ofile = open(self.file_name, 'w')
                ofile.write(str(self.queue))
                ofile.close()

            except Exception as e:
                print("error at writing file ", self.file_name)
                print(e)
        
        self.save_ct += 1
        return

    def change_max_amount(self, new_max_amount):
        self.max_amount = new_max_amount
        return
    # connect db and get most recent data from db or dynamically
    # not made anything with db yet
    def get_data(self, num=100):

        print(self.queue)

        length = self.length

        if num > length:
            return self.queue
        else:
            sub_list = self.queue[-num:length]
            return sub_list


class MigrationDecModel(BaseModel):
    message_id: int
    status: str


class TemperatureModel(BaseModel):
    power: str
    flag: str
    env_temp_cur: str
    now_timestamp: str
    future_timestamp: str
    env_temp_15min: str
    power_future_15min: str


class MaintenanceModel(BaseModel):
    power: str
    flag: str
    now_timestamp: str
    future_timestamp: str
    power_future_15min: str
    positive_3p: str
    negative_3p: str
    positive_7p: str
    negative_7p: str


class MigrationModel(BaseModel):
    pms: dict
    ratio: dict


class MigrationPrimeModel(BaseModel):
    runningPms: list
    offPms: list


class SaveMigrationModel(BaseModel):
    status: str
    data: dict


queue_maintenance = Queue("maintenance_save.json")
queue_temperature = Queue("temperature_save.json")
queue_migration = Queue("migration_save.json")
queue_migration_prime = Queue("migration_prime_save.json")
queue_migration.change_max_amount(1)
queue_migration_prime.change_max_amount(1)

# queue = Queue()
# mainintenance_queue = Queue()
# migration_queue = Queue()


@app.get("/prom/aver")
async def get_last_10_min_average_data():
    
    ip_dict = get_ips()
    data_holder = {}
    
    for server in ip_dict:
        data_holder[server] = handle_aver_last_min(ip_dict[server])

    return data_holder


@app.get('/prom/snmp/cur_power')
async def get_current_powers_computes():
    return get_snmps()


@app.get('/prom/stress/high')
async def start_high_stress():
    try:
        node_ip = "10.150.1.34"

        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:

            result = c.run("nohup stress -c 12 -t 10m >/dev/null 2>&1 &", hide=True)
            return {"status": "success"}

    except Exception as e:
        print(e)


@app.get('/prom/stress/mid')
async def start_mid_stress():
    try:
        node_ip = "10.150.1.34"

        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:

            result = c.run("nohup stress -c 8 -t 10m >/dev/null 2>&1 &", hide=True)
            return {"status": "success"}

    except Exception as e:
        print(e)


@app.get('/prom/stress/low')
async def start_low_stress():
    try:
        node_ip = "10.150.1.34"

        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:

            result = c.run("nohup stress -c 4 -t 10m >/dev/null 2>&1 &", hide=True)
            return {"status": "success"}

    except Exception as e:
        print(e)


@app.get('/prom/stress/stop')
async def stop_stress():
    try:
        node_ip = "10.150.1.34"

        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:

            result = c.run("bash /home/ubuntu/stop_sc.sh", hide=True)
            return {"status": "success"}

    except Exception as e:
        print(e)


@app.get('/prom/snmp/n_min_aver_power/{i}')
async def get_last_n_min_powers_computes(i: int):

    data = get_actual_snmps_nmin(i)
    modified_data = {
    key: {
        new_key.replace("pdu_", ""): value for new_key, value in data[key].items()
    }
    for key in data.keys()
    }

    return modified_data


@app.get("/prom/snmp/min")
async def get_snmp_min_aveage(db: Session = Depends(get_db)):

    data = db.query(SnmpMin).all()
    empty_d = {}
    titles = ["time_stamp", "voltage", "current", "pf", "energy", "power"]
    print(data[0]) 
    l = str(data[0].snmpdata).split(',')

    print(len(l), len(titles))
    for i in range(len(titles)):
        empty_d[titles[i]] = l[i]

    return empty_d


@app.get('/prom/snmpcsv/hour/{computename}')
async def get_snmp_csv_data_hour(computename: str):

    compute = computename.split('&')[0]
    n = int(computename.split('&')[1])
    
    get_snmps_nmin(n, 'h', compute)

    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')


@app.get('/prom/snmpcsv/day/{computename}')
async def get_snmp_csv_data_day(computename: str):
    
    compute = computename.split('&')[0]
    n = int(computename.split('&')[1])

    get_snmps_nmin(n, 'd', compute)
    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')


@app.get('/prom/snmpcsv/minute/{computename}')
async def get_snmp_csv_data_minute(computename:str):
    compute = computename.split('&')[0]
    n = int(computename.split('&')[1])

    get_snmps_nmin(n, compute_name=compute)
    
    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')


@app.get("/prom/mixed/aver30")
async def get_30_sec_average_data_mixed(db: Session = Depends(get_db)):

    posts = db.query(Snmp_30sec).all()
    initi = [0,0,0,0, 0]
    emp = {}
    titles = ["voltage", "current", "pf", "energy", "power"]

    for post in posts:
        adata = post.snmpdata
        # print(post.snmpdata)
        l = adata.split(',')
        td = l[0]
        l = l[1:len(l)]
        
        # t = post.timedata

        for index in range(len(l)):
            initi[index] += float(l[index])
            # c=index

    for i in range(len(initi)):

        emp[titles[i]] = round(initi[i]/len(posts), 4)

    print(len(initi), len(l))
    print(len(post.snmpdata))
    # print(initi)
    # return emp # {"data": initi}
    # posts = db.query
    # return return_mixed_part()
    dc = {**return_mixed_part(), **emp}
    # dc["ts"] = td
    return dc # {**return_mixed_part(), **emp}["ts"] = td
    # didnt work out neither
    # return(emp.update(return_mixed_part()))
    
    # return return_mixed_part() | emp
    # naah for Python 3.9, too lazy to upgrade


@app.get("/prom/aver/lastmin/{minu}")
async def get_last_n_min_average_data(minu: int):

    ip_dict = get_ips()
    data_holder = {}
    print(ip_dict)
    
    idle_dc = {}

    for server in ip_dict:

        data_holder[server] = handle_aver_last_min(ip_dict[server], False, int(minu))
    
    return data_holder

    try:
        node_ip = "10.150.1.30"

        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:

            result = c.run("python3 -c '{}'".format(script_vm_mac_details), hide=True)

            res = eval(result.stdout)
            res = res['result']
            for i in res:
                res[i]['ram'] = float(res[i]['ram']) / 1024

    except Exception as e:
        print(e)
    
    for i in res:
        if 'ip' in res[i].keys():

            ip = res[i]["ip"]
            name = i
            if ip in data_holder.keys():

                idle_dc[name] = data_holder[ip]

    idle_dc['compute3'] = data_holder['10.150.1.34']
    idle_dc['compute2'] = data_holder['10.150.1.33']
    
    return idle_dc


@app.get("/prom/cur")
async def get_current_prometheus_data():

    ip_dict = get_ips()
    data_holder = {}

    for server in ip_dict:
        data_holder[server] = return_cur(ip_dict[server])

    return data_holder


@app.get("/prom/snmps/cur")
async def get_computes_snmp_cur_data():
    return scraper_dict_cr()



@app.get("/prom/snmp/cur")
async def get_snmp_cur_data(db: Session = Depends(get_db)):
    
    compute3_power = get_name_snmp()['compute3']
    post = db.query(Snmp_cur).first()
    emp = {}
    titles = ["voltage", "current", "pf", "energy", "power"]

    l = post.snmpdata.split(',')
    l = l[1:len(l)]

    for i in range(len(l)):

        emp[titles[i]] = round(float(l[i]), 4)
    
    emp['power'] = str(compute3_power)
    return emp


@app.get("/prom/snmp")
async def get_snmp_10_min_data(db: Session = Depends(get_db)):
     
    posts = db.query(Snmp_10).all()
    initi = [0,0,0,0, 0]
    emp = {}
    titles = ["voltage", "current", "pf", "energy", "power"]

    for post in posts:
        adata = post.snmpdata
        # print(post.snmpdata)
        l = adata.split(',')
        l = l[1:len(l)]
        t = post.timedata
        
        for index in range(len(l)):
            initi[index] += float(l[index])
            # c=index
   
    for i in range(len(initi)):

        emp[titles[i]] = round(initi[i]/len(posts), 4)

    # print(initi)
    return emp # {"data": initi}
    # posts = db.query

"""
@app.get("/prom/last/{stri}")
def get_last_n_time_average_data(stri: str):

    match = re.search(r'day=(\d+);hour=(\d+);minute=(\d+)', stri)

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
    else:
        print("Pattern not found in the endpoint string.")


@app.get("/prom/interval/{stri}")
def get_an_interval_average_data(stri: str):
    
    start_match = re.search(r'start=(\d{2}):(\d{2})_(\d{2})_(\d{2})_(\d{4})', input_string)
    end_match = re.search(r'end=(\d{2}):(\d{2})_(\d{2})_(\d{2})_(\d{4})', input_string)
    if start_match and end_match:
        start_hour = int(start_match.group(1))
        start_minute = int(start_match.group(2))
        start_day = int(start_match.group(3))
        start_month = int(start_match.group(4))
        start_year = int(start_match.group(5))

        end_hour = int(end_match.group(1))
        end_minute = int(end_match.group(2))
        end_day = int(end_match.group(3))
        end_month = int(end_match.group(4))
        end_year = int(end_match.group(5))

    ...
"""

@app.get("/prom/smoothaver/{nhour}")
async def get_smooth_n_hour_data(nhour: int):
    return handle_aver_last_min(0, last10=None, go_hour_back=nhour)


@app.get("/prom/day/{nday}")
async def get_last_n_day_csv_data_and_download(nday:int):
    cmd = ["ls ../out"]
    organize_data(nday)

    # pass
    return FileResponse("/home/ubuntu/out/thefactory/1.csv")

import json


@app.get('/prom/pm_mac_details')
async def get_physical_mac_details():

    try:
        res = rq.get("http://10.150.1.30:5001/get-pm-conf").json()

        for i in res:
            res[i]['idle consumption'] = 114
            res[i]["memory_mb"] = float(res[i]["memory_mb"]) / 1024
            # res[i]['memory_mb'] = float(res[i]['memory_mb']
            
        return {"res": res}

    except Exception as e:
        print(e)


@app.get('/prom/vm_mac_details')
async def get_mac_details():
    res = rq.get("http://10.150.1.30:5001/get-vm-conf").json()
        
    res = res['result']
    for i in res:
        res[i]['ram'] = float(res[i]['ram']) / 1024

    return {"res": res}


@app.get('/prom/monitoring')
async def get_monitoring():
    mon_conf = rq.get("http://10.150.1.30:5001/get-moni-conf").json()
    return mon_conf


"""
@app.get("/prom/phy_mac/{iplast}")
async def get_psutil_script_data_phy_machine(iplast):
    try:
        # Establish an SSH connection to the remote node
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        node_ip = "10.150.1." + iplast

        ssh.connect(node_ip, username="ubuntu", password="blc2022*")
        # Define the script to run on the remote node
        script = '''
import psutil

memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')

cpu_count = psutil.cpu_count()

total_memory = memory.total
available_memory = memory.available
used_memory = memory.used
free_memory = memory.free

disk_total = disk.total
disk_used = disk.used
disk_free = disk.free

print(f"{{'total_memory': {{total_memory}}, 'available_memory': {{available_memory}}, 'used_memory': {{used_memory}}, 'free_memory': {{free_memory}}, 'disk_total': {{disk_total}}, 'disk_used': {{disk_used}}, 'disk_free': {{disk_free}}}}}")
        '''

        # Execute the script on the remote node
        stdin, stdout, stderr = ssh.exec_command(script_vm_mac_details)
        data = stdout.read().decode('utf-8')
        ssh.close()

        return JSONResponse(content=data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

        """


# return success in post models
@app.post('/prom/push/maintenance_data')
async def push_chart_data_maintenance(data: MaintenanceModel):
    queue_maintenance.push(data)
    print(data)

    return data


@app.post('/prom/push/temperature_data')
async def push_chart_data_temperature(data: TemperatureModel):
    queue_temperature.push(data)
    print(data)

    return data


@app.post('/prom/migration/decisions')
async def get_migration_decisions(data: MigrationDecModel):
    print(data)
    print(type(data))
    for message in message_ew['messages']:
        if data.message_id == message['message_id'] and data.status == 'decline':
            message['show'] = 0
            print(message_ew)


@app.post('/prom/save/migration')
async def save_new_migration(data: SaveMigrationModel):
    print(data)


@app.post('/prom/push/migration_data')
async def push_chart_data_migration(data: MigrationModel):
    queue_migration.push(data)
    print(data)

    return data
# return success


@app.post('/prom/push/migration_data_prime')
async def push_chart_data_migration_prime(data: MigrationPrimeModel):
    queue_migration_prime.push(data)
    print(data)

    return data


@app.get('/prom/get_chart_data/temperature/{n}')
async def get_n_chart_data(n: int):
    data = queue_temperature.get_data(n)
    # print(data)
    return {"data": data}


@app.get('/prom/get_chart_data/temperature')
async def get_all_chart_data():
    data = queue_temperature.get_data()
    # print(data)
    return {"data": data}


@app.get('/prom/get_chart_data/maintenance/{n}')
async def get_n_chart_data(n: int):
    data = queue_maintenance.get_data(n)
    # print(data)
    return {"data": data}


@app.get('/prom/get_chart_data/maintenance')
async def get_all_chart_data():
    data = queue_maintenance.get_data()
    # print(data)
    return {"data": data}


@app.get('/prom/get_chart_data/migration/{n}')
async def get_all_chart_data():
    data = queue_migration.get_data(n)
    
    data = {"data": data}
    
    return data


@app.get('/prom/get_chart_data/migration')
async def get_all_chart_data():
    data = queue_migration.get_data()
    data = {"data":data } 
    return data


@app.get('/prom/migration/message')
async def get_migration_messages():
    return message_ew
    # return {'messages': [{'message': 'Virtual machine s88 can be migrated to compute3 from compute2. It will possibly save 14.6 watts meaning %2.7 energy saving.', 'show': 1, 'message_id': 1}, {'message': 'Virtual machine Redmine can be migrated to compute2 from compute3. It will possibly save 4.0 watts meaning %0.7 energy saving.', 'show': 1, 'message_id': 2}]}


@app.get("/prom/get_chart_data/migrationprime")
async def get_migration_primer():
    
    data = queue_migration_prime.get_data()
    return {"data": data}


@app.get("/prom/phy_mac/{iplast}")
async def get_psutil_script_data_phy_machine(iplast):
    try:
        node_ip = "10.150.1." + iplast
        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            c.run("pip install psutil", hide=True)
            result = c.run("python3 -c '{}'".format(script_phy_mac), hide=True)
            # c.run("pip install psutil", hide=True)
            return {"res":result.stdout}
    except Exception as e:
        return {error: f"An error occurred: {e}"}
            

# @app.get('/prom/random_migrate')
# def random_migrator(migrate_model: RandomMigrate):
#     ...


