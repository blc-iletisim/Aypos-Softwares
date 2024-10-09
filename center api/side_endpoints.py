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

message_ew = {'messages': [{
                               'message': 'Current power utilization :420.5 Watt <br>Proposed power utilization: 405.3<br>Expected power gain: %3.58',
                               'show': 1, 'message_id': 1}]}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
async def get_snmp_csv_data_minute(computename: str):
    compute = computename.split('&')[0]
    n = int(computename.split('&')[1])

    get_snmps_nmin(n, compute_name=compute)

    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')


@app.get("/prom/mixed/aver30")
async def get_30_sec_average_data_mixed(db: Session = Depends(get_db)):
    posts = db.query(Snmp_30sec).all()
    initi = [0, 0, 0, 0, 0]
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
        emp[titles[i]] = round(initi[i] / len(posts), 4)

    print(len(initi), len(l))
    print(len(post.snmpdata))
    # print(initi)
    # return emp # {"data": initi}
    # posts = db.query
    # return return_mixed_part()
    dc = {**return_mixed_part(), **emp}
    # dc["ts"] = td
    return dc  # {**return_mixed_part(), **emp}["ts"] = td
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
    initi = [0, 0, 0, 0, 0]
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
        emp[titles[i]] = round(initi[i] / len(posts), 4)

    # print(initi)
    return emp  # {"data": initi}
    # posts = db.query


@app.get("/prom/day/{nday}")
async def get_last_n_day_csv_data_and_download(nday: int):
    cmd = ["ls ../out"]
    organize_data(nday)

    # pass
    return FileResponse("/home/ubuntu/out/thefactory/1.csv")
