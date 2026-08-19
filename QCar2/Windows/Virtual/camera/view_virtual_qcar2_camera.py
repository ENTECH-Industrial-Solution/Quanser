import cv2
import time
import sys
import threading
import numpy as np

# นำเข้าคลังไลบรารี QVL ของ Quanser
try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# Multi-Threaded Camera Worker (คลาสดึงภาพกล้องแบบแยก Thread เพื่อความลื่นไหลสูงสุด)
# ==============================================================================
class QLabsCameraThread:
    """ คลาสสำหรับดึงภาพจากกล้องทั้ง 4 ตัวแยกออกไปทำงานใน Background Thread 
        ช่วยแก้ปัญหากล้องกระตุกเนื่องจาก TCP Socket Latency 100% """
    def __init__(self, myCar):
        self.myCar = myCar
        self.frames = {'front': None, 'back': None, 'left': None, 'right': None}
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._fetch_loop, daemon=True)

    def start(self):
        self.thread.start()

    def _fetch_loop(self):
        while self.running:
            sf, img_f = self.myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_FRONT)
            sb, img_b = self.myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_BACK)
            sl, img_l = self.myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_LEFT)
            sr, img_r = self.myCar.get_image(camera=QLabsQCar2.CAMERA_CSI_RIGHT)

            with self.lock:
                if sf and img_f is not None: self.frames['front'] = img_f
                if sb and img_b is not None: self.frames['back'] = img_b
                if sl and img_l is not None: self.frames['left'] = img_l
                if sr and img_r is not None: self.frames['right'] = img_r
            
            time.sleep(0.005) # หน่วงเวลาเล็กน้อยเพื่อไม่ให้ CPU โหลดเกิน

    def get_latest_frames(self):
        with self.lock:
            return (
                self.frames['front'],
                self.frames['back'],
                self.frames['left'],
                self.frames['right']
            )

    def stop(self):
        self.running = False

# ==============================================================================
# Helper Functions สำหรับวาดและรวม Layout
# ==============================================================================
def add_camera_label(img, title, color_bg=(0, 140, 0)):
    """ ฟังก์ชั่นสำหรับวาด Header Label ป้ายชื่อกล้องกำกับส่วนบนของภาพ """
    if img is None:
        return img
    
    h, w = img.shape[:2]
    annotated = img.copy()

    # วาดแถบป้ายชื่อด้านบนภาพ (Header Banner)
    cv2.rectangle(annotated, (0, 0), (w, 32), color_bg, -1)
    cv2.putText(annotated, title, (10, 22), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    
    # วาดเส้นขอบรอบภาพ
    cv2.rectangle(annotated, (0, 0), (w-1, h-1), color_bg, 2)
    
    return annotated

def make_blank_frame(width=480, height=360, text="No Frame"):
    """ สร้างภาพสีดำทดแทนในกรณีที่กำลังเชื่อมต่อกล้อง """
    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(img, text, (width//6, height//2), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    return img

def combine_frames(f_front, f_back, f_left, f_right, layout_mode='2x2'):
    """
    ฟังก์ชั่นในข้อ 5 สำหรับปรับรูปแบบการเรียงของช่องกล้อง:
    - '2x2'        : แบบตาราง 2x2 (หน้า-หลัง / ซ้าย-ขวา)
    - 'horizontal' : แบบเรียงแนวนอน 4 กล้องยาวในแถวเดียว
    - 'vertical'   : แบบเรียงแนวตั้ง 4 กล้องยาวในคอลัมน์เดียว
    """
    if layout_mode == 'horizontal':
        return np.hstack((f_front, f_back, f_left, f_right))
    elif layout_mode == 'vertical':
        return np.vstack((f_front, f_back, f_left, f_right))
    else:  # Default '2x2'
        top_row = np.hstack((f_front, f_back))
        bottom_row = np.hstack((f_left, f_right))
        return np.vstack((top_row, bottom_row))

# ==============================================================================
# Main Program Loop
# ==============================================================================
def main():
    print("==================================================")
    print("  QCar2 Virtual Smooth Multi-Layout Camera Stream ")
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

    # 2. ผูกการเชื่อมต่อกับตัวรถ QCar2 (Actor Number = 1)
    car_id = 1
    myCar = QLabsQCar2(qlabs)
    myCar.actorNumber = car_id

    # 3. เริ่มต้น Background Thread สำหรับดึงภาพกล้องลื่นไหลระดับ 30+ FPS
    cam_fetcher = QLabsCameraThread(myCar)
    cam_fetcher.start()

    print(f"✓ เริ่มสตรีมมิ่งภาพลื่นไหล (Multi-Threaded) จากกล้อง CSI 4 ทิศทาง...")
    print("\n--------------------------------------------------")
    print("🎮 คำสั่งสลับรูปแบบ Layout หน้าต่าง (กดปุ่มบนคีย์บอร์ด):")
    print("   [ 1 ] : สลับการแสดงผลเป็นแบบ [ 2x2 Grid ] (ตาราง)")
    print("   [ 2 ] : สลับการแสดงผลเป็นแบบ [ Horizontal ] (แนวนอน)")
    print("   [ 3 ] : สลับการแสดงผลเป็นแบบ [ Vertical ] (แนวตั้ง)")
    print("   [ Q ] หรือ [ ESC ] : ปิดโปรแกรม")
    print("📌 สามารถใช้เม้าส์ดึงย่อ/ขยายขนาดหน้าต่างภาพได้อย่างอิสระ!")
    print("--------------------------------------------------\n")

    window_name = "QCar2 Quad Camera View [RESIZABLE WINDOW]"
    
    # 4. ตั้งค่าหน้าต่าง OpenCV แบบ WINDOW_NORMAL เพื่อให้สามารถย่อ/ขยายขนาดหน้าต่างได้อย่างอิสระ
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1024, 728) # ขนาดเริ่มต้น

    cam_width = 480
    cam_height = 360
    
    # โหมดการเรียงเริ่มต้น: '2x2', 'horizontal', 'vertical'
    current_layout = '2x2'

    try:
        while True:
            # ดึงภาพล่าสุดจาก Background Thread
            img_front, img_back, img_left, img_right = cam_fetcher.get_latest_frames()

            # ปรับขนาดเฟรมย่อยให้เท่ากัน
            frame_front = cv2.resize(img_front, (cam_width, cam_height)) if img_front is not None else make_blank_frame(cam_width, cam_height, "FRONT CAMERA CONNECTING...")
            frame_back  = cv2.resize(img_back, (cam_width, cam_height))  if img_back is not None  else make_blank_frame(cam_width, cam_height, "BACK CAMERA CONNECTING...")
            frame_left  = cv2.resize(img_left, (cam_width, cam_height))  if img_left is not None  else make_blank_frame(cam_width, cam_height, "LEFT CAMERA CONNECTING...")
            frame_right = cv2.resize(img_right, (cam_width, cam_height)) if img_right is not None else make_blank_frame(cam_width, cam_height, "RIGHT CAMERA CONNECTING...")

            # ติด Label ป้ายชื่อกล้อง
            labeled_front = add_camera_label(frame_front, " FRONT CAMERA ", color_bg=(0, 160, 0))     # สีเขียว
            labeled_back  = add_camera_label(frame_back,  " BACK CAMERA ",   color_bg=(160, 0, 0))     # สีน้ำเงิน
            labeled_left  = add_camera_label(frame_left,  " LEFT CAMERA ",   color_bg=(0, 140, 200))   # สีส้ม
            labeled_right = add_camera_label(frame_right, " RIGHT CAMERA ",  color_bg=(160, 0, 160))   # สีม่วง

            # 5. เรียกฟังก์ชั่นรวมช่องตามโหมดจัดเรียง (2x2 / horizontal / vertical)
            grid_content = combine_frames(labeled_front, labeled_back, labeled_left, labeled_right, layout_mode=current_layout)

            # วาดแถบป้าย Header ด้านบนสุด
            header = np.zeros((35, grid_content.shape[1], 3), dtype=np.uint8)
            cv2.putText(header, f"QCar2 360 Vision (Actor {car_id}) | Layout: [{current_layout.upper()}] | Press [1: 2x2 | 2: Horizontal | 3: Vertical]", 
                        (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

            final_combined_view = np.vstack((header, grid_content))

            # แสดงผลในหน้าต่าง OpenCV (รองรับการย่อขยาย)
            cv2.imshow(window_name, final_combined_view)

            # 6. รับปุ่มกดสลับโหมด หรือ ปิดโปรแกรม
            key = cv2.waitKey(15) & 0xFF
            if key == ord('q') or key == 27:
                print("\nกำลังปิดการสตรีมมิ่งกล้อง...")
                break
            elif key == ord('1'):
                current_layout = '2x2'
                print("[LAYOUT SWITCHED] -> 2x2 Grid View")
            elif key == ord('2'):
                current_layout = 'horizontal'
                print("[LAYOUT SWITCHED] -> Horizontal View")
            elif key == ord('3'):
                current_layout = 'vertical'
                print("[LAYOUT SWITCHED] -> Vertical View")

    except KeyboardInterrupt:
        print("\nหยุดการทำงานโดยผู้ใช้ (Ctrl+C)")
    finally:
        cam_fetcher.stop()
        cv2.destroyAllWindows()
        print("✓ ปิดหน้าต่างสตรีมมิ่งเรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
