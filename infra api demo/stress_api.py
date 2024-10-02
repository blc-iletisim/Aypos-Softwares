from flask import Flask, jsonify, request
from stressor import *

app = Flask(__name__)


@app.route('/start-stress', methods=['POST'])
def start_server():
    data = request.get_json()

    vm_ip = data.get("server_ip")
    
    run_bash_script_on_vm(vm_ip, bash_script, pem_key_path)
    ...

    return {"status": 1}


if __name__ == '__main__':
    app.run(port=5001, host='0.0.0.0', debug=False)

