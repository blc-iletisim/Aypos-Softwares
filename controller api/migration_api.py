from api_functions import *
from create_machines import *
from delete_machines import *


@app.route('/stress', methods=['POST'])
def stressss():

    data = eval(request.get_json())
    server = data.get('vm')
    
    server_id = get_id_vm(server)

    server = conn.compute.get_server(server_id)

    conn.compute.wait_for_server(server)

    addrs = server.addresses[network_name][ip_number]['addr']
    stat = run_bash_script_on_vm(addrs, bash_script, pem_key_path)
    return jsonify({"stat": stat})


@app.route('/migrate', methods=['POST'])
def migrate_server():
    auth_key = request.headers.get('X-Auth-Key')
    
    if auth_key != API_KEY:
        return jsonify({'message': 'Unauthorized'}), 401

    data = eval(request.get_json())
    print(data)
    print(type(data))

    server = data.get("vm_name")
    
    if server == "prometheus_serverV3":
        return {"better not": "break prometheus instance"}

    migrate_to = data.get("to_host")
    server_id = get_id_vm(server)
    server = conn.compute.get_server(server_id)
    
    check_start_server(server, server_id)

    ...
    
    try:

        stat = conn.compute.live_migrate_server(server_id, host=migrate_to, force=True, block_migration=True)
        
        server = conn.compute.get_server(server_id)
        
        conn.compute.wait_for_server(server)
        
        # addrs = server.addresses[network_name][which_ip]['addr']
        # rq.get("http://10.150.1.111:5001/start-stress", json=str({"server_ip": addrs}))    
        # stat = run_bash_script_on_vm(addrs, bash_script, pem_key_path)

        return jsonify({"status": stat, "status_code": 0, })

    except Exception as e:

        return jsonify({"response": str(e), "status_code": 1}), 500


@app.route('/start-instance', methods=['POST'])
def start_server():

    auth_key = request.headers.get('X-Auth-Key')
    if auth_key != API_KEY:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()

    server = data.get("server")
    at_zone = data.get("from")

    ...

    return {"status": 1}


@app.route('/shutoff-instances', methods=['GET'])
def stop_servers():

    auth_key = request.headers.get('X-Auth-Key')
    if auth_key != API_KEY:
        return jsonify({'message': 'Unauthorized'}), 401
    
    vm_names = []

    vms = get_virtual_machines()
    for server_object in vms:
        if server_object.status == 'ACTIVE' and server_object.name != prometheus_vm_openstack_name:
            print(server_object)
            conn.compute.stop_server(server_object)
            vm_names.append(server_object.name)

    ...

    return jsonify({"status": "success", "shutoff_vms": vm_names}), 200


@app.route('/get-vm-conf', methods=['GET'])
def get_vm_conf_api():
    return jsonify(get_vm_conf())


@app.route('/get-pm-conf', methods=['GET'])
def get_pm_conf_api():

    conf = get_pm_conf()
    print(conf)
    return jsonify(conf)


@app.route('/get-all-pm-conf', methods=['GET'])
def get_pm_conf_api():

    conf = get_pm_conf(get_all=True)
    print(conf)
    return jsonify(conf)


@app.route('/get-moni-conf', methods=['GET'])
def get_moni_conf():

    conf = get_monitoring_con()

    return jsonify(conf)


@app.route('/create-vms/<int:num_vms>', methods=['GET'])
def create_vms(num_vms):
    ips_allocated = create_random_vms(num_vms)
    return jsonify({"res": 1})

# delete_vms


@app.route('/delete-vms/<int:num_vms>', methods=['GET'])
def delete_vms_e(num_vms):
    delete_vms(num_vms)
    return jsonify({"res": 1})


@app.route('/create-instances', methods=['GET'])
def create_instances():
    ips = create_random_vms()
    return jsonify({"ips": ips})


@app.route('/get-all-vm-details', methods=['GET'])
def create_instances():
    details = get_all_vm_details()
    return jsonify({"details": details})


if __name__ == '__main__':
    app.run(port=flask_port, host=flask_host, debug=False)

