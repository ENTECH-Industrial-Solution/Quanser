import cv2
import numpy as np
import time
from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2

try:
    from ultralytics import YOLO
    has_yolo = True
except ImportError:
    has_yolo = False
    print("Ultralytics YOLO not found. Displaying raw 360 vision instead.")

# 1. เชื่อมต่อกับเซิร์ฟเวอร์ QLabs
qlabs = QuanserInteractiveLabs()
print("Connecting to QLabs for Digital Twin 360 Vision...")
connected = False
for attempt in range(5):
    if qlabs.open("localhost"):
        connected = True
        print("Successfully connected to QLabs!")
        break
    print(f"Waiting for QLabs server (Attempt {attempt+1}/5)...")
    time.sleep(2)

if not connected:
    print("Error: Unable to connect to QLabs! Please make sure QLabs is running.")
    input("Press Enter to exit...")
    exit()

if has_yolo:
    print("Loading YOLOv8 model for 360 Vision...")
    myYolo = YOLO('yolov8n.pt')

# 2. เลือกตัวละครรถ QCar2 ใน QLabs (เริ่มต้นคันที่ 1)
myCar = QLabsQCar2(qlabs)
myCar.actorNumber = 1

print(f"Streaming Digital Twin 360 Vision... Press 'q' or 'ESC' to stop.")

imageWidth = 640
imageHeight = 480

# ขอบสีดำสำหรับคั่นภาพกล้องแต่ละตัวตามมาตรฐาน Quanser 360 Vision
horizontalBlank = np.zeros((20, 4*imageWidth + 120, 3), dtype=np.uint8)
verticalBlank = np.zeros((imageHeight, 20, 3), dtype=np.uint8)

no_frame_count = 0

# 3. ลูปหลักดึงภาพกล้อง CSI 4 ทิศทางจาก Virtual QCar2 ใน QLabs
while True:
    # ดึงภาพจากกล้องเสมือนทั้ง 4 ตัวของ Virtual QCar2
    success_f, img_front = myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_FRONT)
    success_b, img_back  = myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_BACK)
    success_l, img_left  = myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_LEFT)
    success_r, img_right = myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_RIGHT)

    if not (success_f and success_b and success_l and success_r):
        no_frame_count += 1
        if no_frame_count > 25:
            # หากคันปัจจุบันไม่ได้สตรีมภาพ ให้สลับไปลองคันถัดไป (1 -> 2 -> 3)
            myCar.actorNumber = (myCar.actorNumber % 3) + 1
            print(f"Waiting for 360 CSI cameras... Switched search to QCar2 actorNumber={myCar.actorNumber}")
            no_frame_count = 0
        time.sleep(0.1)
        continue

    no_frame_count = 0

    # ตัดแบ่งภาพกล้องหลังออกเป็นฝั่งขวา [320:640] และฝั่งซ้าย [0:320] เพื่อนำไปไว้ขอบสุดทั้งสองข้าง
    rear_right_half = img_back[:, 320:640]
    rear_left_half  = img_back[:, 0:320]

    # เรียงต่อภาพ 360 องศาตามคู่มือ Quanser 360 Vision:
    # [กล้องหลัง-ขวา] | [กล้องซ้าย] | [กล้องหน้า] | [กล้องขวา] | [กล้องหลัง-ซ้าย]
    middle_row = np.concatenate((
        verticalBlank, 
        rear_right_half, 
        verticalBlank, 
        img_left, 
        verticalBlank, 
        img_front, 
        verticalBlank, 
        img_right, 
        verticalBlank, 
        rear_left_half, 
        verticalBlank
    ), axis=1)

    image360 = np.concatenate((horizontalBlank, middle_row, horizontalBlank), axis=0)

    # นำภาพ 360 องศาไปประมวลผลผ่าน YOLOv8
    if has_yolo:
        results = myYolo(image360, classes=[0, 2, 9, 11], verbose=False)
        display_img = results[0].plot()
        cv2.putText(display_img, f"Digital Twin 360 Vision (Actor {myCar.actorNumber}) - Detected: {len(results[0].boxes)} objects", 
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
    else:
        display_img = image360
        cv2.putText(display_img, f"Digital Twin 360 Vision (Actor {myCar.actorNumber})", 
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

    cv2.imshow('Virtual QCar2 - Digital Twin 360 Vision', display_img)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

cv2.destroyAllWindows()
qlabs.close()
print("Done!")
