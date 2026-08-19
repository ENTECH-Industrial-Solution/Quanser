# from paramiko import SSHClient
# import os
# import time

# client = SSHClient()
# client.load_system_host_keys()
# client.connect('192.168.2.11',username="nvidia",password="nvidia")
# client.exec_command("cd ~/Documents ; python yolov8_client_img_stream.py")
# time.sleep(2)
# client.close()

from paramiko import SSHClient, AutoAddPolicy
import os
import time

LOCAL_SCRIPT = r"C:\Users\Jirapat Chumaungphan\Documents\Quanser\QCar2\Windows\Virtual + Physical\yolov8_client_img_stream.py"
REMOTE_SCRIPT = "/home/nvidia/Documents/yolov8_client_img_stream.py"
QCAR_IP = "192.168.2.11"

client = SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(AutoAddPolicy())

try:
    print(f"Connecting to {QCAR_IP}...")
    client.connect(QCAR_IP, username="nvidia", password="nvidia")
    print("Connected!")

    # อัปโหลดสคริปต์ล่าสุดขึ้น Jetson ก่อนรันเสมอ
    print(f"Uploading yolov8_client_img_stream.py to Jetson...")
    sftp = client.open_sftp()
    sftp.put(LOCAL_SCRIPT, REMOTE_SCRIPT)
    sftp.close()
    print("Upload complete! Running YOLO model on Jetson...")

    stdin, stdout, stderr = client.exec_command(
        'bash -ic "cd ~/Documents ; python yolov8_client_img_stream.py"',
        get_pty=True
    )

    # อ่านและแสดงผลลัพธ์จาก Jetson เพื่อให้หน้าต่างค้างไว้และแสดง Log
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(1024).decode('utf-8', errors='ignore'), end="")
        if stdout.channel.recv_stderr_ready():
            print(stdout.channel.recv_stderr(1024).decode('utf-8', errors='ignore'), end="")
        time.sleep(0.1)

    print(f"\nCommand finished with exit status: {stdout.channel.recv_exit_status()}")

except KeyboardInterrupt:
    print("\nStopping by user...")
except Exception as e:
    print(f"\nAn error occurred: {e}")
finally:
    client.close()
    input("Press Enter to exit...")
