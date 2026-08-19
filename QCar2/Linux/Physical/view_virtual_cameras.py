import cv2
from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
import numpy as np
import time

try:
    from ultralytics import YOLO
    has_yolo = True
except ImportError:
    has_yolo = False
    print("Ultralytics YOLO not found. Displaying raw images instead.")

# 1. เชื่อมต่อกับเซิร์ฟเวอร์ QLabs
qlabs = QuanserInteractiveLabs()
print("Connecting to QLabs...")
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
    # โหลดโมเดล YOLOv8 ตัวเล็กสุด (yolov8n.pt)
    print("Loading YOLOv8 model...")
    myYolo = YOLO('yolov8n.pt')

# 2. เชื่อมต่อกับรถ QCar2 คันที่ 1 (actorNumber = 1) เท่านั้น
myCar = QLabsQCar2(qlabs)
myCar.actorNumber = 1

print(f"Streaming cameras for QCar2 (actorNumber={myCar.actorNumber})... Press 'q' or 'ESC' to stop.")

no_frame_count = 0

# 3. วนลูปดึงภาพมาแสดงผล
while True:
    # ดึงภาพจากกล้อง RGB (RealSense - 640x480)
    success_rgb, rgb_img = myCar.get_image(camera=QLabsQCar2.CAMERA_RGB)
    
    # ดึงภาพจากกล้อง Depth (RealSense - 640x480)
    success_depth, depth_img = myCar.get_image(camera=QLabsQCar2.CAMERA_DEPTH)

    if not (success_rgb and success_depth):
        no_frame_count += 1
        if no_frame_count % 30 == 1:
            print(f"Waiting for QCar2 (actorNumber=1) camera frames... Please make sure QCar2_Virtual_Car1 is running in virtual mode (-virtual_only 1).")
        time.sleep(0.1)
        continue

    no_frame_count = 0
    if has_yolo:
        # ให้ YOLO ประมวลผลภาพ RGB (classes: 0=person, 2=car, 9=traffic light, 11=stop sign)
        results = myYolo(rgb_img, classes=[0, 2, 9, 11], verbose=False)
        
        # วาดกรอบสี่เหลี่ยมลงบนภาพ
        display_img = results[0].plot()
        
        y_offset = 30
        cv2.putText(display_img, f"Detected: {len(results[0].boxes)} objects", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # หาพิกัดตรงกลางของกรอบเพื่อไปเทียบกับระยะ Depth
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            name = myYolo.names[cls_id]
            conf = float(box.conf[0])
            
            # พิกัดกรอบ (x1, y1, x2, y2)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            # ป้องกันพิกัดทะลุขอบภาพ
            y1_c, y2_c = max(0, y1), min(depth_img.shape[0], y2)
            x1_c, x2_c = max(0, x1), min(depth_img.shape[1], x2)
            
            # ดึงภาพ Depth จากทั้งกรอบ Bounding Box ของวัตถุ (เพื่อตรวจจับเสา/โคมไฟจราจร/คน ได้เต็มพื้นที่)
            box_depth = depth_img[y1_c:y2_c, x1_c:x2_c]

            if len(box_depth.shape) == 3:
                box_vals = box_depth[:, :, 0]
            else:
                box_vals = box_depth
                
            # กรองเอาเฉพาะค่าพิกเซลที่มีข้อมูลจริง (มากกว่า 0)
            valid_vals = box_vals[box_vals > 0]

            if len(valid_vals) > 0:
                # ใช้ 25th Percentile เพื่อจับระยะของส่วนหน้าที่ใกล้ที่สุดของวัตถุชิ้นนั้น
                depth_val = float(np.percentile(valid_vals, 25))
                MAX_DEPTH_METERS = 20.0
                dist_m = (depth_val / 255.0) * MAX_DEPTH_METERS
                
                label_dist = f"{name}: {dist_m:.2f}m"
                text = f"{name} ({conf:.2f}) -> Dist: {dist_m:.2f}m (Val:{int(depth_val)})"
                marker_color = (0, 255, 0) # จุดเขียวเมื่อวัดระยะสำเร็จ
            else:
                depth_val = 0
                label_dist = f"{name}: Out of Range"
                text = f"{name} ({conf:.2f}) -> Out of Range"
                marker_color = (128, 128, 128)
            
            # วาดจุดมาร์กเกอร์ตรงจุดกึ่งกลางวัตถุ
            cv2.circle(display_img, (cx, cy), 4, marker_color, -1)
            
            # แสดงข้อความระยะทางเหนือกรอบ Bounding Box
            cv2.putText(display_img, label_dist, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # พิมพ์และแสดงรายละเอียดทางมุมซ้ายบน
            print(f"YOLO Found: {text}")
            y_offset += 25
            cv2.putText(display_img, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    else:
        display_img = rgb_img
        cv2.putText(display_img, "YOLO: Please wait for pip install", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Virtual QCar - YOLO RGB Camera', display_img)
    cv2.imshow('Virtual QCar - Depth Camera', depth_img)

    # รอรับคำสั่งคีย์บอร์ด 1 ms (กด q หรือ ESC เพื่อออกจากลูป)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

cv2.destroyAllWindows()
qlabs.close()
print("Done!")
