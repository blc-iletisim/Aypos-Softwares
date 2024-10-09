api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="
instance_name = "aypostest10"


import requests as rq
import json
header = {"X-Auth-Key": api_key}

mig_req = {"vm_name": "aypostest8", "to_host": "compute4"}

resp = rq.post("http://10.150.1.30:5001/migrate", json=str(mig_req), headers=header)

# print(resp.text)
print(resp.status_code)
print(resp.text)
print(resp.json())
