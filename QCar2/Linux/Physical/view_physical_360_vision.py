import socket
import sys
import os
import time
import cv2
import numpy as np
from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy
from pal.utilities.probe import ObserverAgent

# Ensure QLabs library path is loaded if needed
qvl_path = r"C:\Users\Jirapat Chumaungphan\Documents\Quanser\0_libraries\python"
if qvl_path not in sys.path:
    sys.path.append(qvl_path)

# Try importing Ultralytics YOLO
try:
    from ultralytics import YOLO
    has_yolo_lib = True
except ImportError:
    has_yolo_lib = False
    print("Warning: Ultralytics YOLO not installed. Running in raw 360 Vision mode.")

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
qcar_ip = "192.168.2.56"

print("==================================================================")
print(" Physical QCar2 - 360 Panoramic Vision with YOLOv8 Detection")
print("==================================================================")
print(f"Local Host PC IP : {pc_ip}")
print(f"Physical QCar2 IP: {qcar_ip}")
print("-> Press 'y' to toggle YOLOv8 Object Detection ON / OFF")
print("-> Press 's' to save a screenshot")
print("-> Press 'q' or 'ESC' to quit")
print("==================================================================")

# 1. Load YOLOv8 Model (General Object Detection)
myYolo = None
enable_yolo = True
if has_yolo_lib:
    print("Loading YOLOv8 model for general object detection...")
    try:
        myYolo = YOLO('yolov8n.pt')
        print("YOLOv8 model loaded successfully!")
    except Exception as e:
        print(f"Could not load YOLO model: {e}")
        enable_yolo = False

# 2. Setup Observer Server for receiving 360 camera stream
imageHeight = 480
imageWidth = 640
scaled_h = (imageHeight + 40) // 2  # 260
scaled_w = (4 * imageWidth + 120) // 2  # 1340

port = 18801
uriAddress = f'tcpip://localhost:{port}'
print(f"Initializing PC Observer Stream Server on port {port}...")

agent = ObserverAgent(
    uriAddress=uriAddress,
    id=1,
    bufferSize=scaled_h * scaled_w * 3,
    buffer=np.zeros((scaled_h, scaled_w, 3), dtype=np.uint8),
    agentType=0,
    properties={'name': 'Physical 360 CSI', 'imageSize': [scaled_h, scaled_w, 3], 'scalingFactor': 2}
)

# 3. Connect to Physical QCar2 via SSH to start 4 CSI camera streaming
client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy())

# Distinct color palette for different classes
COLOR_PALETTE = [
    (0, 255, 0),    # Green (Person)
    (255, 128, 0),  # Blue/Orange (Car, vehicles)
    (0, 215, 255),  # Yellow (Traffic sign, light)
    (255, 0, 128),  # Pink/Purple
    (0, 165, 255),  # Orange
    (180, 105, 255),# Hot pink
    (255, 255, 0),  # Cyan
    (50, 205, 50)   # Lime green
]

def draw_camera_regions(img, width, height):
    '''Draw subtle camera zone markers at the bottom of the 360 panoramic view'''
    segments = [
        ("REAR-R", 10, 170),
        ("LEFT", 180, 500),
        ("FRONT", 510, 830),
        ("RIGHT", 840, 1160),
        ("REAR-L", 1170, 1330)
    ]
    for name, x1, x2 in segments:
        cv2.putText(img, name, (x1 + 10, height - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1, cv2.LINE_AA)
        cv2.line(img, (x1, height - 25), (x1, height), (70, 70, 70), 1)

try:
    print(f"Connecting to Physical QCar2 ({qcar_ip}) via SSH...")
    client.connect(qcar_ip, username="nvidia", password="nvidia", timeout=10)
    print("Connected to Physical QCar2!")

    print("Terminating any previous 360 camera processes on QCar2...")
    client.exec_command("pkill -9 -f imaging_360")
    time.sleep(1)

    # Sync probe script to Jetson
    probe_script_path = r"C:\Users\Jirapat Chumaungphan\Documents\Quanser\5_research\sdcs\qcar2\hardware\applications\360_vision\QCar2_imaging_360_probe.py"
    if os.path.exists(probe_script_path):
        print("Syncing QCar2_imaging_360_probe.py to Jetson...")
        sftp = client.open_sftp()
        sftp.put(probe_script_path, "/home/nvidia/Documents/QCar2_imaging_360_probe.py")
        sftp.close()

    cmd = f'bash -ic "cd ~/Documents ; python QCar2_imaging_360_probe.py -ip {pc_ip}"'
    print(f"Launching 4 CSI Cameras on Physical QCar2...")
    client.exec_command(cmd)

    print("\nStreaming 360 Panoramic Vision with YOLOv8 General Detection...\n")

    frame_counter = 0
    fps = 0.0
    fps_timer = time.time()
    last_boxes = None

    while True:
        if not agent.connected:
            agent.check_connection()

        if agent.connected:
            recvFlag, exitCond = agent.receive()
            if recvFlag:
                frame_360 = agent.server.receiveBuffer.copy()
                frame_counter += 1
                display_img = frame_360.copy()
                h_orig, w_orig = frame_360.shape[:2]

                # Calculate running FPS
                now = time.time()
                if frame_counter % 10 == 0:
                    fps = 10.0 / (now - fps_timer) if (now - fps_timer) > 0 else 30.0
                    fps_timer = now

                detected_counts = {}
                total_detected = 0

                # Run YOLOv8 General Object Detection
                if enable_yolo and myYolo is not None:
                    results = myYolo(frame_360, conf=0.35, verbose=False)
                    boxes = results[0].boxes

                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            name = myYolo.names[cls_id]
                            conf = float(box.conf[0])

                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cx = (x1 + x2) // 2
                            cy = (y1 + y2) // 2

                            # Pick color by class id
                            color = COLOR_PALETTE[cls_id % len(COLOR_PALETTE)]

                            # Draw bounding box & center point
                            cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
                            cv2.circle(display_img, (cx, cy), 3, (0, 0, 255), -1)

                            # Label tag
                            label_text = f"{name} {conf:.2f}"
                            (lbl_w, lbl_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                            lbl_y1 = max(0, y1 - lbl_h - 4)
                            cv2.rectangle(display_img, (x1, lbl_y1), (x1 + lbl_w + 4, y1), color, -1)
                            cv2.putText(display_img, label_text, (x1 + 2, y1 - 2),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

                            detected_counts[name] = detected_counts.get(name, 0) + 1
                            total_detected += 1

                # Draw camera zone boundaries and labels
                draw_camera_regions(display_img, w_orig, h_orig)

                # Draw Top Status Bar
                status_color = (30, 30, 30)
                cv2.rectangle(display_img, (0, 0), (w_orig, 28), status_color, -1)

                yolo_status_str = "ON" if enable_yolo else "OFF"
                status_text = f"360 Panoramic Vision | YOLO: {yolo_status_str} | FPS: {fps:.1f}"

                if total_detected > 0:
                    breakdown_str = ", ".join([f"{k}: {v}" for k, v in detected_counts.items()])
                    summary_text = f"Objects ({total_detected}): {breakdown_str}"
                else:
                    summary_text = "Objects: None detected"

                cv2.putText(display_img, status_text, (10, 19),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(display_img, summary_text, (450, 19),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(display_img, "[Y: Toggle YOLO | S: Screenshot | Q: Quit]", (w_orig - 330, 19),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

                cv2.imshow('Physical QCar2 - 360 Vision (YOLOv8 Detection)', display_img)
            else:
                time.sleep(0.005)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('y') or key == ord('Y'):
            enable_yolo = not enable_yolo
            mode_str = "ENABLED" if enable_yolo else "DISABLED"
            print(f"\n[YOLO] Object Detection {mode_str}\n")
        elif key == ord('s') or key == ord('S'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qcar2_360_detection_{timestamp}.jpg"
            cv2.imwrite(filename, display_img)
            print(f"\n[SCREENSHOT] Saved screenshot as: {filename}\n")

except KeyboardInterrupt:
    print("\nStopping 360 Camera View...")
except Exception as e:
    print(f"\nError occurred: {e}")
finally:
    print("Terminating remote camera process, closing SSH and destroying windows...")
    try:
        client.exec_command("pkill -9 -f imaging_360")
        time.sleep(0.5)
        client.close()
    except Exception:
        pass
    try:
        agent.terminate()
    except Exception:
        pass
    cv2.destroyAllWindows()
    print("Done!")
