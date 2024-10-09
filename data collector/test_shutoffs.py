import requests as rq


def shut_off_instance():
    api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="
    header = {"X-Auth-Key": api_key}
    resp = rq.get("http://10.150.1.30:5001/shutoff-instances", headers=header)
    return resp.json()


# print(shut_off_instance())
