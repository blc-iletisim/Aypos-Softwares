import ansible_runner
import inspect
from get_n_lineinv import *

print(inspect.getargspec(ansible_runner.run))
print(dir(ansible_runner))


def ansible_runners(vm_num):
    change_pup_inv(vm_num+1)
    r = ansible_runner.run(playbook='/home/casper/installer/node_exporter.yml', inventory="/home/casper/installer/puppet_inventory")
    print("{}: {}".format(r.status, r.rc))
    # successful: 0

    r = ansible_runner.run(playbook='/home/casper/installer/stress_sender.yml', inventory="/home/casper/installer/puppet_inventory")
    print("{}: {}".format(r.status, r.rc))


if __name__=='__main__':
    ansible_runners(5)

