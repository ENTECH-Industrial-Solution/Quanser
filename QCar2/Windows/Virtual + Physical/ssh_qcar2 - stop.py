from paramiko import SSHClient
import os
import time

client = SSHClient()
client.load_system_host_keys()
client.connect('192.168.2.56',username="nvidia",password="nvidia")
client.exec_command("pkill -15 python")
time.sleep(2)
client.close()