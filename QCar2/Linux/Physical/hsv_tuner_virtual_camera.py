import cv2
import numpy as np
import time
import sys
import json
import os

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2

# ==============================================================================
# QCar2 Virtual CSI Camera Interactive HSV Color Tuner Tool (JSON Auto-Save)
# เครื่องมือสำหรับปรับแต่งหาค่าสี HSV และบันทึกลงไฟล์ hsv_config.json อัตโนมัติ
# ==============================================================================

CONFIG_FILE = "hsv_config.json"

# ค่าเริ่มต้นถ้าไม่มีไฟล์ JSON
default_config = {
    "yellow_lower": [14, 60, 90],
    "yellow_upper": [36, 255, 255],
    "white_lower": [0, 0, 185],
    "white_upper": [180, 30, 255],
    "crop_top_pct": 0.58
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                print(f"Loaded existing HSV config from {CONFIG_FILE}")
                return cfg
        except Exception as e:
            print(f"Error loading config: {e}")
    return default_config

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"\nSuccessfully saved HSV parameters to '{CONFIG_FILE}'!")
        print(json.dumps(cfg, indent=2))
        print("============================================================\n")
    except Exception as e:
        print(f"Error saving config: {e}")

cfg = load_config()

print("=============================================================")
print(" QLabs Virtual Camera Interactive HSV Tuner & JSON Exporter")
print("=============================================================")
print("Connecting to QLabs Server...")

qlabs = QuanserInteractiveLabs()
if not qlabs.open("localhost"):
    print("Error: Cannot connect to QLabs! Please make sure QLabs Simulator is running.")
    sys.exit(1)

print("Successfully connected to QLabs!")

virtualCar = QLabsQCar2(qlabs)
virtualCar.actorNumber = 1

def nothing(x):
    pass

# สร้างหน้าต่างควบคุม Trackbars สำหรับปรับแต่งค่าสี
win_controls = "HSV Trackbars & Controls"
cv2.namedWindow(win_controls, cv2.WINDOW_NORMAL)
cv2.resizeWindow(win_controls, 480, 550)

# กำหนดค่าเริ่มต้นจาก JSON
cv2.createTrackbar("Yellow H Min", win_controls, cfg["yellow_lower"][0], 180, nothing)
cv2.createTrackbar("Yellow H Max", win_controls, cfg["yellow_upper"][0], 180, nothing)
cv2.createTrackbar("Yellow S Min", win_controls, cfg["yellow_lower"][1], 255, nothing)
cv2.createTrackbar("Yellow S Max", win_controls, cfg["yellow_upper"][1], 255, nothing)
cv2.createTrackbar("Yellow V Min", win_controls, cfg["yellow_lower"][2], 255, nothing)
cv2.createTrackbar("Yellow V Max", win_controls, cfg["yellow_upper"][2], 255, nothing)

cv2.createTrackbar("White H Min", win_controls, cfg["white_lower"][0], 180, nothing)
cv2.createTrackbar("White H Max", win_controls, cfg["white_upper"][0], 180, nothing)
cv2.createTrackbar("White S Min", win_controls, cfg["white_lower"][1], 255, nothing)
cv2.createTrackbar("White S Max", win_controls, cfg["white_upper"][1], 255, nothing)
cv2.createTrackbar("White V Min", win_controls, cfg["white_lower"][2], 255, nothing)
cv2.createTrackbar("White V Max", win_controls, cfg["white_upper"][2], 255, nothing)

crop_init = int(cfg.get("crop_top_pct", 0.58) * 100)
cv2.createTrackbar("Crop Top %", win_controls, crop_init, 90, nothing)

print("\nAdjust trackbars to isolate yellow & white lines.")
print("Press 's' or 'p' to SAVE config to 'hsv_config.json'.")
print("Press 'q' or 'ESC' to save & exit.\n")

try:
    while True:
        # อ่านค่าจาก Trackbars
        yh_min = cv2.getTrackbarPos("Yellow H Min", win_controls)
        yh_max = cv2.getTrackbarPos("Yellow H Max", win_controls)
        ys_min = cv2.getTrackbarPos("Yellow S Min", win_controls)
        ys_max = cv2.getTrackbarPos("Yellow S Max", win_controls)
        yv_min = cv2.getTrackbarPos("Yellow V Min", win_controls)
        yv_max = cv2.getTrackbarPos("Yellow V Max", win_controls)

        wh_min = cv2.getTrackbarPos("White H Min", win_controls)
        wh_max = cv2.getTrackbarPos("White H Max", win_controls)
        ws_min = cv2.getTrackbarPos("White S Min", win_controls)
        ws_max = cv2.getTrackbarPos("White S Max", win_controls)
        wv_min = cv2.getTrackbarPos("White V Min", win_controls)
        wv_max = cv2.getTrackbarPos("White V Max", win_controls)

        crop_pct = cv2.getTrackbarPos("Crop Top %", win_controls) / 100.0

        current_cfg = {
            "yellow_lower": [yh_min, ys_min, yv_min],
            "yellow_upper": [yh_max, ys_max, yv_max],
            "white_lower": [wh_min, ws_min, wv_min],
            "white_upper": [wh_max, ws_max, wv_max],
            "crop_top_pct": float(round(crop_pct, 2))
        }

        # ดึงภาพกล้อง Virtual CSI Front Camera
        success, img_front = virtualCar.get_image(camera=QLabsQCar2.CAMERA_CSI_FRONT)
        if not success or img_front is None:
            time.sleep(0.05)
            continue

        h, w = img_front.shape[:2]
        crop_y1 = int(h * crop_pct)
        cropped = img_front[crop_y1:h, :].copy()

        hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)

        # คำนวณ Mask สีเหลืองและสีขาว
        lower_yellow = np.array([yh_min, ys_min, yv_min])
        upper_yellow = np.array([yh_max, ys_max, yv_max])
        mask_yellow  = cv2.inRange(hsv, lower_yellow, upper_yellow)

        lower_white = np.array([wh_min, ws_min, wv_min])
        upper_white = np.array([wh_max, ws_max, wv_max])
        mask_white  = cv2.inRange(hsv, lower_white, upper_white)

        # สร้างภาพซ้อนทับสำหรับแสดงผล
        overlay = cropped.copy()
        pts_yellow = np.argwhere(mask_yellow > 0)
        pts_white  = np.argwhere(mask_white > 0)

        # แสดงเส้นสีเหลืองเป็นสีแดง (RED)
        if len(pts_yellow) > 0:
            overlay[pts_yellow[:, 0], pts_yellow[:, 1]] = [0, 0, 255]

        # แสดงเส้นสีขาวเป็นสีเขียว (GREEN)
        if len(pts_white) > 0:
            overlay[pts_white[:, 0], pts_white[:, 1]] = [0, 255, 0]

        disp_img = img_front.copy()
        disp_img[crop_y1:h, :] = overlay
        cv2.line(disp_img, (0, crop_y1), (w, crop_y1), (0, 255, 255), 2)

        # เขียนข้อความค่าสีปัจจุบันลงบนภาพ
        cv2.putText(disp_img, f"Yellow: [{yh_min},{ys_min},{yv_min}] - [{yh_max},{ys_max},{yv_max}] (Pts: {len(pts_yellow)})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        cv2.putText(disp_img, f"White:  [{wh_min},{ws_min},{wv_min}] - [{wh_max},{ws_max},{wv_max}] (Pts: {len(pts_white)})",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        # แสดงหน้าต่างผลลัพธ์
        cv2.imshow("Virtual CSI Camera - Detected Lanes Overlay", cv2.resize(disp_img, (640, 320)))
        cv2.imshow("Mask Yellow (Center Line)", cv2.resize(mask_yellow, (400, 200)))
        cv2.imshow("Mask White (Road Edge)", cv2.resize(mask_white, (400, 200)))

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q') or key == 27:
            save_config(current_cfg)
            break
        elif key == ord('s') or key == ord('p'):
            save_config(current_cfg)

except KeyboardInterrupt:
    pass
finally:
    cv2.destroyAllWindows()
    qlabs.close()
    print("HSV Tuner Closed.")
