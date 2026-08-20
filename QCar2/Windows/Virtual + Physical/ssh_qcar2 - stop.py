from paramiko import SSHClient
import json
import os
import time

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "network_config.json")) as f:
    QCAR_IP = json.load(f)["qcar_ip"]

client = SSHClient()
client.load_system_host_keys()
client.connect(QCAR_IP,username="nvidia",password="nvidia")
client.exec_command("pkill -15 python")
time.sleep(2)
client.close()