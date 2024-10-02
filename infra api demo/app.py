from fastapi import FastAPI
import uvicorn
from remove_sshold import *
from ansible_run import *

app = FastAPI()


@app.get('/')
def a():
    return {1:1}


@app.get('/remove_known')
def  remov():
    remove_all_sshs()
    return {"result": "success"}


@app.get('/start_ansible/{vm_number}')
def  start_ansible(vm_number:int):
    # remove_all_sshs()
    ansible_runners(vm_number)
    return {"result":"success"}


uvicorn.run(app, host='0.0.0.0')

