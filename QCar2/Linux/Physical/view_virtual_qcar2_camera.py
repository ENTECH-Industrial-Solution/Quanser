import cv2
import time
import sys
import numpy as np

# นำเข้าคลังไลบรารี QVL ของ Quanser
try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QCar2 Virtual Camera Viewer (Camera Only)
# สคริปต์สำหรับการเปิดและแสดงผลภาพกล้องจากรถ QCar2 ใน QLabs (แยกเดี่ยว)
# ==============================================================================

def main():
    print("==================================================")
    print("   QCar2 Virtual Camera Viewer (Camera Only)      ")
    print("==================================================")

    # 1. เชื่อมต่อกับ QLabs Server
    qlabs = QuanserInteractiveLabs()
    print("กำลังเชื่อมต่อกับ QLabs (localhost)...")
    
    connected = False
    for attempt in range(5):
        if qlabs.open("localhost"):
            connected = True
            print("✓ เชื่อมต่อ QLabs สำเร็จ!")
            break
        print(f"กำลังรอการเชื่อมต่อ QLabs... (ลองครั้งที่ {attempt+1}/5)")
        time.sleep(1.5)

    if not connected:
        print("\n[ERROR] ไม่สามารถเชื่อมต่อกับ QLabs ได้!")
        print("กรุณาเปิดโปรแกรม Quanser Interactive Labs (QLabs) ก่อนรันสคริปต์นี้")
        input("กด Enter เพื่อปิด...")
        return

    # 2. เชื่อมต่อกับตัวรถ QCar2 (Actor Number = 1)
    car_id = 1
    myCar = QLabsQCar2(qlabs)
    myCar.actorNumber = car_id

    # 3. ตั้งค่ามุมกล้องมองหลัง (Trailing Camera)
    myCar.possess(QLabsQCar2.CAMERA_TRAILING)
    print("✓ สตรีมมิ่งกล้อง QCar2... (กด 'q' หรือ 'ESC' บนหน้าต่างภาพเพื่อปิด)")

    window_name = "QCar2 Virtual Camera Feed"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    no_frame_count = 0

    try:
        while True:
            # 4. ดึงภาพจากกล้อง RGB (640x480)
            success_rgb, rgb_img = myCar.get_image(camera=QLabsQCar2.CAMERA_RGB)
            
            if not success_rgb or rgb_img is None:
                no_frame_count += 1
                display_img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(display_img, "Waiting for QCar2 Camera Feed...", (100, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                no_frame_count = 0
                display_img = rgb_img.copy()

                # แสดงสถานะมุมกล้อง
                cv2.putText(display_img, f"QCar2 Camera (Actor ID: {car_id})", (15, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow(window_name, display_img)

            # 5. ตรวจสอบการกดปุ่มออกโปรแกรม
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:
                print("\nกำลังปิดการแสดงผลกล้อง...")
                break

    except KeyboardInterrupt:
        print("\nหยุดการทำงานโดยผู้ใช้ (Ctrl+C)")
    finally:
        cv2.destroyAllWindows()
        print("✓ ปิดสตรีมกล้องเรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
