from fastapi import FastAPI, Response
from datetime import datetime
import subprocess

app = FastAPI()


def split_string (data):
    seperator="\""
    parts = data.split(seperator,1)
    return tuple(parts)


def spl (data):
    test = split_string(data)[1]
    test2 = split_string(test)[0]
    return test2

import time


def get_sensor_data():
    start = time.time()
    voltage_1_12 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.3.1.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    voltage_1_12 = float(spl(voltage_1_12))
 
    voltage_13_24 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.3.2.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    voltage_13_24 = float(spl(voltage_13_24))

    curr_compute4 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.8.1.21.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    curr_compute4 = float(spl(curr_compute4))

    curr_compute3 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.8.1.6.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    curr_compute3 = float(spl(curr_compute3))

    # curr_compute
    curr_compute1 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.8.1.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    curr_compute1 = float(spl(curr_compute1))

    curr_compute2 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.8.1.10.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    
    energy_1_12 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.3.1.5.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

    energy_13_24 = subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.3.2.5.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

    curr_compute2 = float(spl(curr_compute2))
    
    energy_1_12 = float(spl(energy_1_12))
    energy_13_24 = float(spl(energy_13_24))

    total_curr_1_12 = curr_compute1 + curr_compute2 + curr_compute3
    currprop1 = curr_compute1 / total_curr_1_12 
    currprop2 = curr_compute2 / total_curr_1_12
    currprop3 = curr_compute3 / total_curr_1_12
    
    energy_comp1 = currprop1 * energy_1_12
    energy_comp2 = currprop2 * energy_1_12
    energy_comp3 = currprop3 * energy_1_12
    energy_comp4 = energy_13_24

    pf_compute1 =  subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.9.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute1 = float(spl(pf_compute1))

    pf_compute2 =  subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.9.10.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute2 = float(spl(pf_compute2))

    pf_compute3 =  subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.9.6.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute3 = float(spl(pf_compute3))

    pf_compute4 =  subprocess.Popen([r"snmpget","-v1","-c","public","10.150.1.93","iso.3.6.1.4.1.30966.7.1.9.21.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute4 = float(spl(pf_compute4))

    end = time.time() 

    print('time takes: ', end-start)
    return (f'pdu_power{{compute_id="compute1"}} {round(curr_compute1*voltage_1_12, 3)}\n'
            f'pdu_power{{compute_id="compute2"}} {round(curr_compute2*voltage_1_12, 3)}\n'
            f'pdu_power{{compute_id="compute3"}} {round(curr_compute3*voltage_1_12, 3)}\n'
            f'pdu_power{{compute_id="compute4"}} {round(curr_compute4*voltage_13_24, 3)}\n'
            f'pdu_pf{{compute_id="compute1"}} {pf_compute1}\n'
            f'pdu_pf{{compute_id="compute2"}} {pf_compute2}\n'
            f'pdu_pf{{compute_id="compute3"}} {pf_compute3}\n'
            f'pdu_pf{{compute_id="compute4"}} {pf_compute4}\n'
            f'pdu_current{{compute_id="compute1"}} {curr_compute1}\n'
            f'pdu_current{{compute_id="compute2"}} {curr_compute2}\n'
            f'pdu_current{{compute_id="compute3"}} {curr_compute3}\n'
            f'pdu_current{{compute_id="compute4"}} {curr_compute4}\n'
            f'pdu_energy{{compute_id="compute1"}} {energy_comp1}\n'
            f'pdu_energy{{compute_id="compute2"}} {energy_comp2}\n'
            f'pdu_energy{{compute_id="compute3"}} {energy_comp3}\n'
            f'pdu_energy{{compute_id="compute4"}} {energy_comp4}\n'
            f'pdu_voltage{{compute_id="compute1"}} {voltage_1_12}\n'
            f'pdu_voltage{{compute_id="compute2"}} {voltage_1_12}\n'
            f'pdu_voltage{{compute_id="compute3"}} {voltage_1_12}\n'
            f'pdu_voltage{{compute_id="compute4"}} {voltage_13_24}\n')

@app.get("/metrics")
async def metrics():
    sensor_data = get_sensor_data()
    print('request: ',  datetime.now())

    return Response(sensor_data, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8099)

