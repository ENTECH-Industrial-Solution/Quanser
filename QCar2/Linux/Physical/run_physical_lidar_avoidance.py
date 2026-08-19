import socket
import sys
import time
import cv2
import numpy as np
import os
import threading
from paramiko import SSHClient, AutoAddPolicy
from pal.utilities.probe import ObserverAgent

# ==============================================================================
# Physical QCar2 LiDAR Avoidance & Virtual SDCSRoadMap Control Launcher (PC)
# ==============================================================================

def get_local_ip():
    '''Find local Host PC IP address connected to QCar2 network'''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.168.2.56', 1))
        IP = s.getsockname()[0]
    except Exception:
        try:
            IP = socket.gethostbyname(socket.gethostname())
        except Exception:
            IP = '192.168.2.82'
    finally:
        s.close()
    return IP

pc_ip = get_local_ip()
qcar_ip = '192.168.2.56'

print("=============================================================")
print(" Option 1: SDCSRoadMap Pure Pursuit & Left Avoidance Launcher")
print("=============================================================")
print(f"Local Host PC IP: {pc_ip}")
print(f"Physical QCar2 IP: {qcar_ip}")

# 1. กำหนดขนาดภาพ Observer Agent (600x400 Composite LiDAR + Telemetry Panel)
img_h = 600
img_w = 400
port = 18801
uriAddress = f'tcpip://localhost:{port}'
print(f"Initializing PC Observer Server on port {port}...")

agent = ObserverAgent(
    uriAddress=uriAddress,
    id=1,
    bufferSize=img_h * img_w * 3,
    buffer=np.zeros((img_h, img_w, 3), dtype=np.uint8),
    agentType=0,
    properties={'name': 'LiDAR Map', 'imageSize': [img_h, img_w, 3], 'scalingFactor': 1}
)

def sftp_sync_dir(sftp, local_dir, remote_dir):
    '''Recursively upload directory to SSH server'''
    try:
        sftp.mkdir(remote_dir)
    except Exception:
        pass
    for item in os.listdir(local_dir):
        l_item = os.path.join(local_dir, item)
        r_item = remote_dir + '/' + item
        if os.path.isfile(l_item):
            sftp.put(l_item, r_item)
        elif os.path.isdir(l_item) and item != '__pycache__':
            sftp_sync_dir(sftp, l_item, r_item)

# 2. เชื่อมต่อ SSH ไปยังรถ Physical QCar2 เพื่อเริ่มรันระบบบนตัวรถจริง
client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy())

def ssh_output_reader(stdout, stderr):
    '''Thread to continuously print stdout and stderr from Jetson SSH command'''
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            text = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
            print(text, end="")
        if stdout.channel.recv_stderr_ready():
            err_text = stdout.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
            print(err_text, end="")
        time.sleep(0.05)

try:
    print(f"Connecting to Physical QCar2 ({qcar_ip}) via SSH...")
    client.connect(qcar_ip, username="nvidia", password="nvidia")
    print("Successfully connected to Physical QCar2!")

    print("Stopping conflicting processes on QCar2...")
    client.exec_command("pkill -9 -f yolov8 ; pkill -9 -f imaging_360 ; pkill -9 -f lidar_avoidance ; pkill -9 -f qcar2_physical_lidar")
    time.sleep(1)

    print("Syncing qcar2_physical_lidar_avoidance.py and qvl library to QCar2...")
    sftp = client.open_sftp()
    
    # Sync main script
    local_script = r"C:\Users\Jirapat Chumaungphan\Documents\Quanser\QCar2\QCar2\qcar2_physical_lidar_avoidance.py"
    sftp.put(local_script, "/home/nvidia/Documents/qcar2_physical_lidar_avoidance.py")

    # Sync qvl library folder so Jetson has full QLabs access
    local_qvl = r"C:\Users\Jirapat Chumaungphan\Documents\Quanser\0_libraries\python\qvl"
    sftp_sync_dir(sftp, local_qvl, "/home/nvidia/Documents/qvl")
    
    sftp.close()

    cmd = f'bash -ic "cd ~/Documents ; python qcar2_physical_lidar_avoidance.py -ip {pc_ip} -qlabs_ip {pc_ip}"'
    print(f"Launching Physical LiDAR Detection & Option 1 Control on QCar2...\n")
    
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

    # Start SSH output logger thread
    log_thread = threading.Thread(target=ssh_output_reader, args=(stdout, stderr), daemon=True)
    log_thread.start()

    print("Running LiDAR Obstacle Avoidance... Press 'q' or 'ESC' on display window to stop.\n")

    # 3. ลูปหลักเปิดรับสตรีมภาพ LiDAR 2D Map + Telemetry Panel จากรถคันจริงมาแสดงบน PC
    while True:
        if not agent.connected:
            agent.check_connection()

        if agent.connected:
            recvFlag, exitCond = agent.receive()
            if recvFlag:
                map_frame = agent.server.receiveBuffer.copy()
                cv2.imshow("Option 1: SDCSRoadMap Pure Pursuit & LiDAR Avoidance", map_frame)
            else:
                time.sleep(0.005)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

except KeyboardInterrupt:
    print("\nStopping LiDAR Obstacle Avoidance System...")
except Exception as e:
    print(f"\nError occurred: {e}")
finally:
    print("\nStopping Physical QCar2 motors & closing SSH...")
    try:
        client.exec_command("pkill -9 -f qcar2_physical_lidar")
    except Exception:
        pass
    client.close()
    cv2.destroyAllWindows()
    print("Done!")
