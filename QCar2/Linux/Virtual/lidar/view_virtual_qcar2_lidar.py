import time
import sys
import threading
import numpy as np
import cv2

# นำเข้าคลังไลบรารี QVL
try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QCar2 Virtual LiDAR Viewer (View-Only Mode)
# สคริปต์แสดงผลแผนที่ 2D Point Cloud จาก LiDAR 360 องศา
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


def draw_lidar_map(angles, distances, map_size=800, max_range=6.0):
    """ สร้างแผนที่ 2D Point Cloud พร้อมวงแหวนระยะทางและสถิติโซนสิ่งกีดขวาง """
    img = np.zeros((map_size, map_size, 3), dtype=np.uint8)
    center = (map_size // 2, map_size // 2)
    pixels_per_meter = (map_size // 2 - 50) / max_range

    num_rings = 4
    ring_step = max_range / num_rings
    for i in range(1, num_rings + 1):
        r = ring_step * i
        radius_px = int(r * pixels_per_meter)
        cv2.circle(img, center, radius_px, (45, 45, 45), 1)
        cv2.putText(img, f"{r:.1f}m", (center[0] + 5, center[1] - radius_px + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)

    cv2.line(img, (center[0], 20), (center[0], map_size - 20), (55, 55, 55), 1)
    cv2.line(img, (20, center[1]), (map_size - 20, center[1]), (55, 55, 55), 1)

    min_front, min_left, min_right, min_rear = 999.0, 999.0, 999.0, 999.0

    if angles is not None and distances is not None and len(distances) > 0:
        deg = np.rad2deg(np.arctan2(np.sin(angles), np.cos(angles)))

        front_mask = (deg >= -30) & (deg <= 30) & (distances > 0.05) & (distances <= max_range)
        left_mask  = (deg > 30)   & (deg <= 110) & (distances > 0.05) & (distances <= max_range)
        right_mask = (deg >= -110) & (deg < -30)  & (distances > 0.05) & (distances <= max_range)
        rear_mask  = ((deg > 110) | (deg < -110)) & (distances > 0.05) & (distances <= max_range)

        if np.any(front_mask): min_front = np.min(distances[front_mask])
        if np.any(left_mask):  min_left  = np.min(distances[left_mask])
        if np.any(right_mask): min_right = np.min(distances[right_mask])
        if np.any(rear_mask):  min_rear  = np.min(distances[rear_mask])

        x_pts = distances * np.cos(angles)
        y_pts = distances * np.sin(angles)

        px = (center[0] + y_pts * pixels_per_meter).astype(np.int32)
        py = (center[1] - x_pts * pixels_per_meter).astype(np.int32)

        for i in range(len(distances)):
            dist = distances[i]
            if dist <= 0.05 or dist > max_range:
                continue

            pt_x, pt_y = px[i], py[i]
            if 0 <= pt_x < map_size and 0 <= pt_y < map_size:
                color = (0, 0, 255) if dist < 0.75 else (0, 165, 255) if dist < 1.5 else (0, 255, 255) if dist < 2.5 else (0, 255, 120)
                cv2.circle(img, (pt_x, pt_y), 3, color, -1)

    cv2.circle(img, center, 12, (0, 0, 255), -1)
    cv2.arrowedLine(img, center, (center[0], center[1] - 30), (0, 255, 0), 2, tipLength=0.3)

    cv2.putText(img, f"QCar2 Virtual 2D LiDAR (Range: {max_range:.1f}m)", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(img, "Press [Z]/[X] or [+]/[-] to Zoom Range | [ESC] to Exit", (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

    def format_dist(val):
        return f"{val:.2f}m" if val < 900 else "CLEAR"

    cv2.putText(img, f"FRONT : {format_dist(min_front)}", (20, map_size - 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255) if min_front < 0.75 else (0, 255, 0), 2)
    cv2.putText(img, f"LEFT  : {format_dist(min_left)}", (20, map_size - 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255) if min_left < 0.75 else (200, 200, 200), 1)
    cv2.putText(img, f"RIGHT : {format_dist(min_right)}", (20, map_size - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255) if min_right < 0.75 else (200, 200, 200), 1)
    cv2.putText(img, f"REAR  : {format_dist(min_rear)}", (20, map_size - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    if min_front < 0.75:
        cv2.putText(img, "!!! WARNING: FRONT OBSTACLE !!!", (map_size // 2 - 160, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    return img


def main():
    print("==================================================")
    print("  QCar2 Virtual 2D LiDAR Viewer (View-Only Mode)  ")
    print("==================================================")

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

    window_name = "QCar2 Virtual - 2D LiDAR Viewer"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 480, 480)

    current_max_range = 6.0

    print("\n--------------------------------------------------")
    print("📡 กำลังแสดงผล 2D LiDAR Point Cloud Map:")
    print("   -> หน้าต่างสามารถปรับย่อ/ขยายขนาดได้อิสระ (Resizable Window)")
    print("   -> กด [ Z ] / [ - ] : ขยายแผนที่ (Zoom Out Range)")
    print("   -> กด [ X ] / [ + ] : ย่อแผนที่ (Zoom In Range)")
    print("   -> กด [ Q ] หรือ [ ESC ] : ปิดโปรแกรม")
    print("--------------------------------------------------\n")

    loop_rate = 0.033

    try:
        while True:
            t_start = time.time()

            angles, distances = lidar_worker.get_data()
            lidar_img = draw_lidar_map(angles, distances, map_size=800, max_range=current_max_range)

            cv2.imshow(window_name, lidar_img)
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
        cv2.destroyAllWindows()
        print("✓ ปิดหน้าต่าง LiDAR Viewer เรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
