import time
import sys
import threading
import numpy as np
import cv2

# นำเข้าคลังไลบรารี QVL และ keyboard
try:
    import keyboard
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารีที่จำเป็น (qvl หรือ keyboard) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QCar2 Virtual Autonomous LiDAR Avoidance & Motor Controller
# สคริปต์ควบคุมรถ QCar2 ด้วยระบบหลบหลีกสิ่งกีดขวางอัตโนมัติ (พร้อมระบบควบคุมคีย์บอร์ดในตัว)
# ==============================================================================

class QLabsLidarThread:
    """ คลาสสำหรับดึงข้อมูล LiDAR แบบแยก Thread เพื่อความลื่นไหลสูงสุด """
    def __init__(self, myCar, num_samples=400):
        self.myCar = myCar
        self.num_samples = num_samples
        self.angles = None
        self.distances = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._fetch_loop, daemon=True)

    def start(self):
        self.thread.start()

    def _fetch_loop(self):
        while self.running:
            success, angles, distances = self.myCar.get_lidar(samplePoints=self.num_samples)
            if success and distances is not None and len(distances) > 0:
                with self.lock:
                    self.angles = angles
                    self.distances = distances
            time.sleep(0.02)  # 50 Hz

    def get_data(self):
        with self.lock:
            return self.angles, self.distances

    def stop(self):
        self.running = False


def main():
    print("==============================================================")
    print("   QCar2 Virtual LiDAR Avoidance & Motor Controller System    ")
    print("==============================================================")

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
        return

    car_id = 1
    myCar = QLabsQCar2(qlabs)
    myCar.actorNumber = car_id

    lidar_worker = QLabsLidarThread(myCar, num_samples=400)
    lidar_worker.start()

    auto_mode = True
    m_key_pressed = False

    window_name = "QCar2 Virtual - LiDAR Avoidance & Control"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 480, 480)

    current_max_range = 6.0

    print("\n--------------------------------------------------------------")
    print("🎮 สคริปต์นี้ควบคุมการขับขี่รถ QCar2 ในตัว:")
    print("   [ M ]         : สลับโหมด (Auto LiDAR Avoidance <-> Manual Control)")
    print("   [ W / S ]     : เดินหน้า / ถอยหลัง (ในโหมด Manual)")
    print("   [ A / D ]     : เลี้ยวซ้าย / เลี้ยวขวา (ในโหมด Manual)")
    print("   [ SPACE ]     : เบรกหยุดรถทันที")
    print("   [ Z / X ]     : Zoom Out / Zoom In ขยายหรือย่อระยะทางแผนที่")
    print("   [ Q / ESC ]   : ออกจากโปรแกรม")
    print("--------------------------------------------------------------\n")

    map_size = 800
    loop_rate = 0.033

    try:
        while True:
            t_start = time.time()

            if keyboard.is_pressed('m') or keyboard.is_pressed('M'):
                if not m_key_pressed:
                    auto_mode = not auto_mode
                    print(f"\n[MODE CHANGE] สลับโหมดเป็น: {'AUTOMATIC (LiDAR Avoidance)' if auto_mode else 'MANUAL CONTROL'}")
                    m_key_pressed = True
            else:
                m_key_pressed = False

            angles, distances = lidar_worker.get_data()

            target_speed = 0.0
            target_steer_deg = 0.0
            left_signal = False
            right_signal = False
            status_text = ""
            status_color = (0, 255, 0)

            min_front, min_left, min_right = 999.0, 999.0, 999.0

            if angles is not None and distances is not None and len(distances) > 0:
                deg = np.rad2deg(np.arctan2(np.sin(angles), np.cos(angles)))

                front_mask = (deg >= -25) & (deg <= 25) & (distances > 0.08) & (distances <= current_max_range)
                left_mask  = (deg > 25)   & (deg <= 85) & (distances > 0.08) & (distances <= current_max_range)
                right_mask = (deg >= -85) & (deg < -25) & (distances > 0.08) & (distances <= current_max_range)

                if np.any(front_mask): min_front = np.min(distances[front_mask])
                if np.any(left_mask):  min_left  = np.min(distances[left_mask])
                if np.any(right_mask): min_right = np.min(distances[right_mask])

            if auto_mode:
                target_speed = 3.0
                target_steer_deg = 0.0
                status_text = "AUTO: CLEAR - FORWARD"
                status_color = (0, 255, 0)

                if min_front < 0.9:
                    if min_left > min_right and min_left > 0.7:
                        target_steer_deg = -25.0
                        target_speed = 1.5
                        left_signal = True
                        status_text = f"AUTO: OBSTACLE FRONT -> AVOID LEFT ({min_front:.2f}m)"
                        status_color = (0, 165, 255)
                    elif min_right > min_left and min_right > 0.7:
                        target_steer_deg = 25.0
                        target_speed = 1.5
                        right_signal = True
                        status_text = f"AUTO: OBSTACLE FRONT -> AVOID RIGHT ({min_front:.2f}m)"
                        status_color = (0, 165, 255)
                    else:
                        target_speed = 0.0
                        target_steer_deg = 0.0
                        status_text = f"AUTO: EMERGENCY STOP ({min_front:.2f}m)"
                        status_color = (0, 0, 255)

                elif min_left < 0.45:
                    target_steer_deg = 15.0
                    right_signal = True
                    status_text = f"AUTO: WARNING CLOSE TO LEFT ({min_left:.2f}m)"
                    status_color = (0, 255, 255)

                elif min_right < 0.45:
                    target_steer_deg = -15.0
                    left_signal = True
                    status_text = f"AUTO: WARNING CLOSE TO RIGHT ({min_right:.2f}m)"
                    status_color = (0, 255, 255)

                if keyboard.is_pressed('space'):
                    target_speed = 0.0
                    target_steer_deg = 0.0
                    status_text = "AUTO: MANUAL BRAKE OVERRIDE"
                    status_color = (0, 0, 255)
            else:
                status_text = "MANUAL CONTROL"
                status_color = (255, 255, 0)

                if keyboard.is_pressed('a') or keyboard.is_pressed('A'):
                    target_steer_deg = -30.0
                    left_signal = True
                elif keyboard.is_pressed('d') or keyboard.is_pressed('D'):
                    target_steer_deg = 30.0
                    right_signal = True

                if keyboard.is_pressed('space'):
                    target_speed = 0.0
                elif keyboard.is_pressed('w') or keyboard.is_pressed('W'):
                    target_speed = 4.0 if not keyboard.is_pressed('shift') else 7.0
                elif keyboard.is_pressed('s') or keyboard.is_pressed('S'):
                    target_speed = -2.5

            if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                break

            myCar.set_velocity_and_request_state_degrees(
                forward=float(target_speed),
                turn=float(target_steer_deg),
                headlights=True,
                leftTurnSignal=left_signal,
                rightTurnSignal=right_signal,
                brakeSignal=(target_speed == 0.0),
                reverseSignal=(target_speed < 0.0)
            )

            map_img = np.zeros((map_size, map_size, 3), dtype=np.uint8)
            center = (map_size // 2, map_size // 2)
            pixels_per_meter = (map_size // 2 - 50) / current_max_range

            num_rings = 4
            ring_step = current_max_range / num_rings
            for i in range(1, num_rings + 1):
                r = ring_step * i
                radius_px = int(r * pixels_per_meter)
                cv2.circle(map_img, center, radius_px, (45, 45, 45), 1)

            if angles is not None and distances is not None:
                x_pts = distances * np.cos(angles)
                y_pts = distances * np.sin(angles)
                px = (center[0] + y_pts * pixels_per_meter).astype(np.int32)
                py = (center[1] - x_pts * pixels_per_meter).astype(np.int32)

                for i in range(len(distances)):
                    dist = distances[i]
                    if 0.05 < dist <= current_max_range:
                        pt_x, pt_y = px[i], py[i]
                        if 0 <= pt_x < map_size and 0 <= pt_y < map_size:
                            color = (0, 0, 255) if dist < 0.9 else (0, 255, 255) if dist < 1.8 else (0, 255, 120)
                            cv2.circle(map_img, (pt_x, pt_y), 3, color, -1)

            cv2.circle(map_img, center, 12, (0, 0, 255), -1)
            steer_rad = np.deg2rad(target_steer_deg)
            arrow_end = (int(center[0] + 30 * np.sin(steer_rad)), int(center[1] - 30 * np.cos(steer_rad)))
            cv2.arrowedLine(map_img, center, arrow_end, (0, 255, 0), 2)

            cv2.putText(map_img, f"QCar2 Virtual - LiDAR Avoidance (Range: {current_max_range:.1f}m)", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.putText(map_img, status_text, (20, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
            cv2.putText(map_img, f"Mode: {'AUTO (LiDAR Avoidance)' if auto_mode else 'MANUAL (Keyboard)'} [Press M to switch]",
                        (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)

            cv2.putText(map_img, f"Front: {min_front:.2f}m | Left: {min_left:.2f}m | Right: {min_right:.2f}m",
                        (20, map_size - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow(window_name, map_img)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                break
            elif key == ord('z') or key == ord('Z') or key == ord('-') or key == ord('_'):
                current_max_range = min(12.0, current_max_range + 1.0)
                print(f"[ZOOM OUT] ขยายระยะแผนที่เพิ่มขึ้นเป็น: {current_max_range:.1f} เมตร")
            elif key == ord('x') or key == ord('X') or key == ord('+') or key == ord('='):
                current_max_range = max(2.0, current_max_range - 1.0)
                print(f"[ZOOM IN] ย่อระยะแผนที่ลงเป็น: {current_max_range:.1f} เมตร")

            t_elapsed = time.time() - t_start
            if t_elapsed < loop_rate:
                time.sleep(loop_rate - t_elapsed)

    except KeyboardInterrupt:
        print("\nหยุดการทำงานโดยผู้ใช้ (Ctrl+C)")
    finally:
        lidar_worker.stop()
        myCar.set_velocity_and_request_state_degrees(0, 0, False, False, False, True, False)
        cv2.destroyAllWindows()
        print("✓ หยุดรถและปิดระบบเรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
