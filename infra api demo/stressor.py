import paramiko

def run_bash_script_on_vm(vm_ip, bash_script, pem_key_path):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=vm_ip, username="ubuntu", key_filename=pem_key_path)

        stdin, stdout, stderr = ssh_client.exec_command(bash_script)

        for line in stdout.readlines():
            print(line.strip())

        ssh_client.close()

    except Exception as e:
        print(f"Error connecting to VM: {e}")

# Example usage:
vm_ip = "10.150.1.130"
bash_script = "/home/ubuntu/randomStressor.sh"
pem_key_path = "/home/casper/ayposTest.pem"

# run_bash_script_on_vm(vm_ip, bash_script, pem_key_path)
