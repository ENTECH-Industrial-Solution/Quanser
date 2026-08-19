import time
import numpy as np
import cv2
from pal.products.qcar import QCar, QCarLidar

# ==============================================================================
# QCar2 LiDAR Obstacle Avoidance & 2D Point Cloud Map
# สคริปต์หลบหลีกสิ่งกีดขวางอัตโนมัติด้วย 2D LiDAR Point Cloud สำหรับ QCar2
# ==============================================================================

print("Initializing QCar Hardware & RP-LiDAR A2 Sensor...")
myCar = QCar()
myLidar = QCarLidar(numMeasurements=360, rangingDistanceMode=2, interpolationMode=0)

# พารามิเตอร์การวาดแผนที่ 2D Point Cloud Map
pixelsPerMeter  = 60
sideLengthScale = 8 * pixelsPerMeter  # ขนาดแผนที่ 480x480 พิกเซล (ครอบคลุมระยะ 8x8 เมตร)
decay           = 0.85                # อัตราการจางลงของจุด Point Cloud เก่า
maxDistance     = 3.5                 # ระยะทำการสูงสุด 3.5 เมตร

lidarMap = np.zeros((sideLengthScale, sideLengthScale, 3), dtype=np.float32)

print("\nStarting LiDAR Obstacle Avoidance System...")
print("-> แสดงแผนที่ 2D Point Cloud Map และสถานะหลบหลีกสิ่งกีดขวางแบบ Real-time")
print("-> กด Ctrl+C หรือกด 'q' บนหน้าต่างแผนที่เพื่อหยุดการทำงาน\n")

try:
    while True:
        # 1. อ่านข้อมูล LiDAR (ระยะทาง distances และมุม angles 360 องศา)
        myLidar.read()
        distances = myLidar.distances
        angles = myLidar.angles

        if distances is None or len(distances) == 0:
            time.sleep(0.03)
            continue

        # แปลงมุมให้อยู่ในระนาบพิกัดของตัวรถ
        anglesInBodyFrame = angles * -1 + np.pi

        # 2. วิเคราะห์โซนสิ่งกีดขวาง 360 องศา (Sector Analysis)
        # แปลงมุมเป็นองศาช่วง [-180, 180] องศา
        deg = np.rad2deg(np.arctan2(np.sin(anglesInBodyFrame), np.cos(anglesInBodyFrame)))

        # กำหนดโซนตรวจสอบ:
        # ด้านหน้า (Front): [-25, +25] องศา
        # ด้านซ้าย (Left):   [+25, +85] องศา
        # ด้านขวา (Right):  [-85, -25] องศา
        front_idx = np.where((deg >= -25) & (deg <= 25)  & (distances > 0.08) & (distances < maxDistance))[0]
        left_idx  = np.where((deg > 25)   & (deg <= 85)  & (distances > 0.08) & (distances < maxDistance))[0]
        right_idx = np.where((deg >= -85) & (deg < -25)  & (distances > 0.08) & (distances < maxDistance))[0]

        min_front = np.min(distances[front_idx]) if len(front_idx) > 0 else 999.0
        min_left  = np.min(distances[left_idx])  if len(left_idx) > 0  else 999.0
        min_right = np.min(distances[right_idx]) if len(right_idx) > 0 else 999.0

        # 3. อัลกอริทึมตัดสินใจการเลี้ยวและความเร็ว (Obstacle Avoidance Control)
        target_speed = 0.3     # ความเร็วเดินหน้าปกติ (m/s)
        target_steering = 0.0 # องศาพวงมาลัย (rad)
        status_text = "CLEAR - FORWARD"
        status_color = (0, 255, 0) # สีเขียว

        # เงื่อนไข 1: มีสิ่งกีดขวางด้านหน้าในระยะอันตราย (< 0.75 เมตร)
        if min_front < 0.75:
            if min_right > min_left and min_right > 0.6:
                # ด้านขวาว่างกว่า -> หักเลี้ยวขวาหลบ
                target_steering = 0.4
                target_speed = 0.15
                status_text = f"OBSTACLE FRONT -> AVOID RIGHT (Dist: {min_front:.2f}m)"
                status_color = (0, 165, 255) # สีส้ม
            elif min_left > min_right and min_left > 0.6:
                # ด้านซ้ายว่างกว่า -> หักเลี้ยวซ้ายหลบ
                target_steering = -0.4
                target_speed = 0.15
                status_text = f"OBSTACLE FRONT -> AVOID LEFT (Dist: {min_front:.2f}m)"
                status_color = (0, 165, 255)
            else:
                # ตันทั้งซ้ายและขวา -> เบรกหยุดฉุกเฉิน
                target_speed = 0.0
                target_steering = 0.0
                status_text = f"EMERGENCY STOP (Front: {min_front:.2f}m)"
                status_color = (0, 0, 255) # สีแดง

        # เงื่อนไข 2: มีสิ่งกีดขวางใกล้ขอบซ้ายเกินไป (< 0.35 เมตร) -> เอียงพวงมาลัยประคองออกขวา
        elif min_left < 0.35:
            target_steering = 0.25
            status_text = f"WARNING: CLOSE TO LEFT (Dist: {min_left:.2f}m)"
            status_color = (0, 255, 255) # สีเหลือง

        # เงื่อนไข 3: มีสิ่งกีดขวางใกล้ขอบขวาเกินไป (< 0.35 เมตร) -> เอียงพวงมาลัยประคองออกซ้าย
        elif min_right < 0.35:
            target_steering = -0.25
            status_text = f"WARNING: CLOSE TO RIGHT (Dist: {min_right:.2f}m)"
            status_color = (0, 255, 255)

        # ส่งคำสั่งควบคุมไปยังมอเตอร์ของ QCar2
        myCar.write(throttle=target_speed, steering=target_steering)

        # 4. วาดแผนที่ 2D Point Cloud Map สำหรับแสดงผล
        lidarMap = decay * lidarMap
        valid_pts = [i for i, v in enumerate(distances) if 0.08 < v < maxDistance]
        if valid_pts:
            x_pts = distances[valid_pts] * np.cos(anglesInBodyFrame[valid_pts])
            y_pts = distances[valid_pts] * np.sin(anglesInBodyFrame[valid_pts])

            pX = np.clip((sideLengthScale/2 - x_pts * pixelsPerMeter).astype(np.int32), 0, sideLengthScale - 1)
            pY = np.clip((sideLengthScale/2 - y_pts * pixelsPerMeter).astype(np.int32), 0, sideLengthScale - 1)

            lidarMap[pX, pY] = [0, 255, 255] # จุด LiDAR แสดงเป็นสีเหลือง

        display_map = np.clip(lidarMap, 0, 255).astype(np.uint8)

        # วาดตำแหน่งตัวรถ QCar2 ตรงกลางแผนที่ (จุดสีแดง + ลูกศรสีเขียวชี้ไปทางด้านหน้า)
        car_center = (int(sideLengthScale/2), int(sideLengthScale/2))
        cv2.circle(display_map, car_center, 7, (0, 0, 255), -1)
        cv2.arrowedLine(display_map, car_center, (car_center[0], car_center[1] - 22), (0, 255, 0), 2)

        # แสดงข้อความสถานะการหลบหลีกและระยะทางแต่ละโซน
        cv2.putText(display_map, status_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
        cv2.putText(display_map, f"Front: {min_front:.2f}m | Left: {min_left:.2f}m | Right: {min_right:.2f}m",
                    (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        cv2.imshow("QCar2 - LiDAR Obstacle Avoidance Map", display_map)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

        time.sleep(0.033)

except KeyboardInterrupt:
    print("\nStopping Obstacle Avoidance System...")
finally:
    # หยุดรถและปิดการเชื่อมต่อฮาร์ดแวร์เพื่อความปลอดภัย
    myCar.write(0, 0)
    myCar.terminate()
    myLidar.terminate()
    cv2.destroyAllWindows()
    print("QCar2 Motors & LiDAR stopped safely.")
