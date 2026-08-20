import time
import json
import numpy as np
import cv2
import argparse
import sys
import os
import math

def _default_host_ip():
    '''Read host_pc_ip_fallback from network_config.json if it was synced alongside this script'''
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network_config.json")
        with open(cfg_path) as f:
            return json.load(f)["host_pc_ip_fallback"]
    except Exception:
        return "192.168.2.82"

# Add local directory to sys.path so qvl module can be loaded if synced locally
sys.path.append(os.path.expanduser('~/Documents'))

from pal.products.qcar import QCar, QCarLidar
from pal.utilities.probe import Probe

try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
    has_qlabs = True
except ImportError:
    has_qlabs = False
    print("Warning: qvl library not found. QLabs virtual car control will be disabled.")

try:
    from hal.products.mats import SDCSRoadMap
    has_roadmap = True
except ImportError:
    has_roadmap = False

# ==============================================================================
# QCar2 Physical LiDAR Avoidance & Virtual QLabs Waypoint Pure Pursuit System
# - Option 1: SDCSRoadMap + Pure Pursuit Controller (100% Robust, No HSV Needed!)
# - Reads Physical RP-LiDAR A2 Sensor on physical QCar2 board
# - Controls Virtual QCar2 Actor in QLabs using Waypoint Pure Pursuit Navigation
# - 1-to-1 Physical Wheel Steering Synchronization with Virtual QCar2
# - 4-State Lane Return FSM with Default LEFT Avoidance Priority
# ==============================================================================

parser = argparse.ArgumentParser(description="Physical LiDAR Detection + Virtual SDCSRoadMap Pure Pursuit Navigation (Option 1)")
parser.add_argument("-ip", "--host_ip", type=str, default=_default_host_ip(), help="Host PC IP for Probe Display")
parser.add_argument("-qlabs_ip", "--qlabs_ip", type=str, default="localhost", help="QLabs Server IP Address")
parser.add_argument("-actor", "--actor_number", type=int, default=1, help="Virtual QCar2 Actor Number in QLabs")
parser.add_argument("--physical_throttle", type=float, default=0.0, help="Physical car throttle (default: 0.0 for wheel steering sync only)")
args = parser.parse_args()

print("=============================================================")
print(" Option 1: SDCSRoadMap Pure Pursuit & Left Avoidance System")
print("=============================================================")
print(f"Host PC IP: {args.host_ip}")
print(f"QLabs IP: {args.qlabs_ip} (Actor #{args.actor_number})")
print(f"Physical Wheels Sync Enabled: TRUE (Throttle: {args.physical_throttle})\n")

# ------------------------------------------------------------------------------
# Pure Pursuit Waypoint Steering Controller Implementation
# ------------------------------------------------------------------------------
def wrap_to_pi(th):
    th = th % (2 * np.pi)
    if th > np.pi:
        th -= 2 * np.pi
    return th

class PurePursuitController:
    def __init__(self, waypoints, k=1.8, max_steer=np.pi/6):
        self.wp = waypoints # 2xN array [x; y]
        self.N = waypoints.shape[1]
        self.wpi = 0
        self.k = k
        self.max_steer = max_steer
        self.ect = 0.0

    def update(self, p, th, speed=0.25):
        wp_1 = self.wp[:, np.mod(self.wpi, self.N - 1)]
        wp_2 = self.wp[:, np.mod(self.wpi + 1, self.N - 1)]

        v = wp_2 - wp_1
        v_mag = np.linalg.norm(v)
        if v_mag == 0:
            return 0.0
        v_uv = v / v_mag

        tangent = np.arctan2(v_uv[1], v_uv[0])
        s = np.dot(p - wp_1, v_uv)

        if s >= v_mag:
            self.wpi = (self.wpi + 1) % (self.N - 1)

        ep = wp_1 + v_uv * s
        ct = ep - p
        dir_val = wrap_to_pi(np.arctan2(ct[1], ct[0]) - tangent)

        self.ect = np.linalg.norm(ct) * np.sign(dir_val)
        psi = wrap_to_pi(tangent - th)

        speed_val = max(abs(speed), 0.1)
        raw_steer = wrap_to_pi(psi + np.arctan2(self.k * self.ect, speed_val))

        return float(np.clip(raw_steer, -self.max_steer, self.max_steer))

    def sync_to_closest(self, p):
        dists = np.linalg.norm(self.wp - p[:, None], axis=0)
        self.wpi = int(np.argmin(dists))

# สร้างข้อมูล Waypoints เส้นทางถนน QLabs Cityscape (SDCSRoadMap Outer Loop)
if has_roadmap:
    try:
        roadmap = SDCSRoadMap(leftHandTraffic=False)
        waypoints = roadmap.generate_path([0, 2, 4, 6, 0]) * 10.0
        print(f"Generated SDCSRoadMap path with {waypoints.shape[1]} waypoints.")
    except Exception as e:
        print(f"SDCSRoadMap init error: {e}. Generating default loop path.")
        waypoints = None
else:
    waypoints = None

if waypoints is None:
    # สร้างทางเลือกวงรอบ Waypoint สำรองใน QLabs Cityscape (Scale 10.0m)
    t_vals = np.linspace(0, 2*np.pi, 200)
    x_w = 17.0 + 15.0 * np.cos(t_vals)
    y_w = 11.0 + 15.0 * np.sin(t_vals)
    waypoints = np.vstack([x_w, y_w])

pp_controller = PurePursuitController(waypoints, k=1.8)

# 1. เชื่อมต่อฮาร์ดแวร์รถจริง QCar2 (readMode=1, frequency=60) และ LiDAR A2
myCar = QCar(readMode=1, frequency=60)
myLidar = QCarLidar(numMeasurements=360, rangingDistanceMode=2, interpolationMode=0)

# 2. เชื่อมต่อกับ QLabs Virtual Server บน Host PC
virtual_connected = False
virtualCar = None

if has_qlabs:
    qlabs = QuanserInteractiveLabs()
    print(f"Connecting to QLabs server at {args.qlabs_ip}...")
    if qlabs.open(args.qlabs_ip):
        virtualCar = QLabsQCar2(qlabs)
        virtualCar.actorNumber = args.actor_number
        virtual_connected = True
        print(f"Successfully connected to QLabs Virtual QCar2 (Actor {args.actor_number})!")
    else:
        print("Warning: Unable to connect to QLabs. Operating in LiDAR sensing-only mode.")
else:
    print("Operating without QLabs library.")

# พารามิเตอร์การวาดแผนที่ 2D Point Cloud และ Probe Stream
map_w = 400
map_h = 400
pixelsPerMeter = 50
decay = 0.85
maxDistance = 4.5

# กำหนด Observer Probe (สตรีมภาพ 400x600 กลับไปแสดงบนหน้าจอ PC)
probe_h = 600
probe_w = 400
probe = Probe(ip=args.host_ip)
probe.add_display(imageSize=[probe_h, probe_w, 3], scaling=False, name="LiDAR Map")
lidarMap = np.zeros((map_h, map_w, 3), dtype=np.float32)

# 3. กำหนดสถานะ 4-State Lane Return Finite State Machine (FSM)
STATE_LANE_KEEPING = 0  # ขับตามเส้นทางเลนด้วย Pure Pursuit Waypoint Navigation
STATE_AVOIDING     = 1  # หักเลี้ยวเบี่ยงออกซ้ายหลบสิ่งกีดขวาง (Avoid Left)
STATE_PASSING      = 2  # ขับตรงแซงขนานสิ่งกีดขวางบนเลนซ้ายให้พ้นระยะปลอดภัย
STATE_RETURNING    = 3  # หักเลี้ยวกลับไปทางขวาเพื่อเข้าเลนเดิม (Return Right)

fsm_state = STATE_LANE_KEEPING
avoid_direction = None   # 'LEFT' หรือ 'RIGHT'
state_start_time = 0.0

# พารามิเตอร์เวลาและมุมสำหรับการเลี้ยวหลบและเลี้ยวกลับ
avoid_duration  = 1.5   # เวลาหักเลี้ยวออก (วินาที)
pass_duration   = 2.2   # เวลาขับแซงขนาน (วินาที)
return_duration = 1.4   # เวลาหักเลี้ยวกลับเข้าเลน (วินาที)
steer_angle     = 0.42  # มุมพวงมาลัยหลบ (rad)

# ซิงค์ตำแหน่ง Waypoint ใกล้เคียงที่สุดในเริ่มต้น
if virtual_connected:
    success, loc, rot, scale = virtualCar.get_world_transform()
    if success:
        p_init = np.array([loc[0], loc[1]])
        pp_controller.sync_to_closest(p_init)

print("\nPhysical LiDAR & SDCSRoadMap Pure Pursuit Active!")
print("-> อ่านค่า LiDAR จริง + คำนวณ Pure Pursuit Waypoint Navigation -> ล้อรถจริงหมุนสัมพันธ์กับ Virtual QCar2...\n")

try:
    while True:
        if not probe.connected:
            probe.check_connection()

        # 4. อ่านข้อมูล LiDAR จากเซนเซอร์จริง
        myLidar.read()
        distances = myLidar.distances
        angles = myLidar.angles

        if distances is None or len(distances) == 0:
            time.sleep(0.03)
            continue

        anglesInBodyFrame = angles * -1 + np.pi
        deg = np.rad2deg(np.arctan2(np.sin(anglesInBodyFrame), np.cos(anglesInBodyFrame)))

        # 5. วิเคราะห์สิ่งกีดขวาง 3 โซน (ด้านหน้า, ซ้าย, ขวา) จาก LiDAR จริง
        front_idx = np.where((deg >= -25) & (deg <= 25)  & (distances > 0.08) & (distances < maxDistance))[0]
        left_idx  = np.where((deg > 25)   & (deg <= 90)  & (distances > 0.08) & (distances < maxDistance))[0]
        right_idx = np.where((deg >= -90) & (deg < -25)  & (distances > 0.08) & (distances < maxDistance))[0]

        min_front = np.min(distances[front_idx]) if len(front_idx) > 0 else 999.0
        min_left  = np.min(distances[left_idx])  if len(left_idx) > 0  else 999.0
        min_right = np.min(distances[right_idx]) if len(right_idx) > 0 else 999.0

        current_time = time.time()

        # 6. อ่านพิกัดตำแหน่งจริงและมุมหันของรถใน QLabs และคำนวณ Pure Pursuit Steering
        car_x, car_y, car_yaw = 0.0, 0.0, 0.0
        waypoint_steering = 0.0

        if virtual_connected:
            success, loc, rot, scale = virtualCar.get_world_transform()
            if success:
                car_x, car_y = loc[0], loc[1]
                car_yaw = rot[2]
                p_car = np.array([car_x, car_y])

                # คำนวณพวงมาลัยจาก Pure Pursuit Controller
                waypoint_steering = pp_controller.update(p_car, car_yaw, speed=0.25)

        # 7. อัลกอริทึม 4-State Lane Return FSM Decision Logic (Safe Passing & Left Priority)
        target_speed = 0.25
        target_steering = 0.0
        left_signal = False
        right_signal = False
        status_text = "LANE KEEPING - PURE PURSUIT"
        status_color = (0, 255, 0) # สีเขียว

        # --- STATE 0: LANE_KEEPING ---
        if fsm_state == STATE_LANE_KEEPING:
            target_speed = 0.25
            target_steering = waypoint_steering
            status_text = f"STATE 0: PURE PURSUIT NAV ({target_steering:+.2f} rad)"
            status_color = (0, 255, 0)

            # เงื่อนไขเปลี่ยนเป็น AVOIDING: Physical LiDAR เจอสิ่งกีดขวางด้านหน้า < 0.75m
            if min_front < 0.75:
                # ลำดับความสำคัญแรก: เบี่ยงออกซ้าย (Avoid Left Priority)
                if min_left > 0.50 or min_left >= min_right:
                    avoid_direction = 'LEFT'
                    fsm_state = STATE_AVOIDING
                    state_start_time = current_time
                    print(f"\n[FSM] Obstacle detected ({min_front:.2f}m) -> Transitioning to STATE 1: AVOIDING LEFT")
                elif min_right > 0.50:
                    avoid_direction = 'RIGHT'
                    fsm_state = STATE_AVOIDING
                    state_start_time = current_time
                    print(f"\n[FSM] Left blocked! -> Fallback Transitioning to STATE 1: AVOIDING RIGHT")
                else:
                    target_speed = 0.0
                    target_steering = 0.0
                    status_text = f"EMERGENCY STOP (Front: {min_front:.2f}m)"
                    status_color = (0, 0, 255)

        # --- STATE 1: AVOIDING (Default LEFT) ---
        elif fsm_state == STATE_AVOIDING:
            target_speed = 0.20
            elapsed = current_time - state_start_time

            if avoid_direction == 'LEFT':
                target_steering = -steer_angle  # หักพวงมาลัยซ้าย
                left_signal = True
                status_text = f"STATE 1: AVOIDING LEFT ({elapsed:.1f}s)"
            else:
                target_steering = steer_angle   # Fallback หักขวา
                right_signal = True
                status_text = f"STATE 1: AVOIDING RIGHT ({elapsed:.1f}s)"
            status_color = (0, 165, 255)

            # เงื่อนไขเปลี่ยนเป็น PASSING: ด้านหน้าโล่งแล้ว และหักเปลี่ยนเลนพ้นระยะเวลา avoid_duration (1.5s)
            if min_front > 0.90 and elapsed >= avoid_duration:
                fsm_state = STATE_PASSING
                state_start_time = current_time
                print(f"[FSM] Avoided obstacle front -> Transitioning to STATE 2: PASSING OBSTACLE")

        # --- STATE 2: PASSING (Safe Passing Distance) ---
        elif fsm_state == STATE_PASSING:
            target_speed = 0.22
            target_steering = 0.0 # วิ่งตรงบนเลนซ้ายที่เบี่ยงออกไป
            elapsed = current_time - state_start_time
            status_text = f"STATE 2: PASSING OBSTACLE ({elapsed:.1f}s)"
            status_color = (255, 255, 0)

            # ตรวจสอบว่าสิ่งกีดขวางพ้นจากด้านข้างแล้วหรือยัง (ด้านข้างต้องโล่งเกิน 0.70m และครบเวลา pass_duration 2.2s)
            obstacle_side_distance = min_right if avoid_direction == 'LEFT' else min_left
            side_is_cleared = (obstacle_side_distance > 0.70)

            if side_is_cleared and elapsed >= pass_duration:
                fsm_state = STATE_RETURNING
                state_start_time = current_time
                print(f"[FSM] Passed obstacle side safely -> Transitioning to STATE 3: RETURNING TO LANE")

        # --- STATE 3: RETURNING (Return RIGHT) ---
        elif fsm_state == STATE_RETURNING:
            target_speed = 0.20
            elapsed = current_time - state_start_time

            # หักพวงมาลัยสวนทางกลับเข้าเลนเดิม
            if avoid_direction == 'LEFT':
                target_steering = steer_angle  # หักขวากลับเข้าเลนเดิม
                right_signal = True
                status_text = f"STATE 3: RETURNING TO LANE (Right - {elapsed:.1f}s)"
            else:
                target_steering = -steer_angle # Fallback หักซ้ายกลับเข้าเลน
                left_signal = True
                status_text = f"STATE 3: RETURNING TO LANE (Left - {elapsed:.1f}s)"
            status_color = (0, 255, 255)

            # เงื่อนไขเปลี่ยนกลับเป็น LANE_KEEPING: หักกลับเข้าเลนเท่ากับเวลาที่เบี่ยงออกไป
            if elapsed >= return_duration:
                fsm_state = STATE_LANE_KEEPING
                avoid_direction = None
                if virtual_connected:
                    p_curr = np.array([car_x, car_y])
                    pp_controller.sync_to_closest(p_curr)
                print(f"[FSM] Returned to original lane -> Resuming STATE 0: PURE PURSUIT NAV\n")

        # 8. ส่งคำสั่งควบคุมไปยัง Virtual QCar2 ใน QLabs
        if virtual_connected:
            virtualCar.set_velocity_and_request_state(
                forward=float(target_speed),
                turn=float(target_steering),
                headlights=True,
                leftTurnSignal=left_signal,
                rightTurnSignal=right_signal,
                brakeSignal=(target_speed == 0.0),
                reverseSignal=False
            )

        # 9. สั่งงานพวงมาลัยและคันเร่งรถจริง Physical QCar2 ด้วย read_write_std ให้ล้อหมุนสัมพันธ์กับ Virtual 100%
        led_array = np.zeros(16, dtype=np.int8)
        if left_signal:
            led_array[0:4] = 1
        elif right_signal:
            led_array[0:4] = 1
            
        myCar.read_write_std(
            throttle=float(args.physical_throttle),
            steering=float(target_steering),
            LEDs=led_array
        )

        # 10. สร้างภาพแผนที่ 2D Point Cloud Map และ Panel ข้อมูล Telemetry ส่งกลับ PC
        lidarMap = decay * lidarMap
        valid_pts = [i for i, v in enumerate(distances) if 0.08 < v < maxDistance]
        if valid_pts:
            x_pts = distances[valid_pts] * np.cos(anglesInBodyFrame[valid_pts])
            y_pts = distances[valid_pts] * np.sin(anglesInBodyFrame[valid_pts])

            pX = np.clip((map_h/2 - x_pts * pixelsPerMeter).astype(np.int32), 0, map_h - 1)
            pY = np.clip((map_w/2 - y_pts * pixelsPerMeter).astype(np.int32), 0, map_w - 1)

            lidarMap[pX, pY] = [0, 255, 255]

        display_map = np.clip(lidarMap, 0, 255).astype(np.uint8)
        car_center = (int(map_w/2), int(map_h/2))
        cv2.circle(display_map, car_center, 6, (0, 0, 255), -1)
        cv2.arrowedLine(display_map, car_center, (car_center[0], car_center[1] - 20), (0, 255, 0), 2)

        cv2.putText(display_map, status_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.40, status_color, 1)
        cv2.putText(display_map, f"F:{min_front:.2f}m L:{min_left:.2f}m R:{min_right:.2f}m", (10, 385), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # สร้าง Telemetry Panel ด้านล่าง (400x200) แสดงพิกัด GPS และ Pure Pursuit Status
        telemetry_panel = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.putText(telemetry_panel, "Option 1: SDCSRoadMap Pure Pursuit Nav", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        cv2.putText(telemetry_panel, f"Virtual Car Pose: X={car_x:+.2f}m, Y={car_y:+.2f}m", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
        cv2.putText(telemetry_panel, f"Yaw: {np.rad2deg(car_yaw):+.1f} deg | Target Steering: {target_steering:+.3f} rad", (10, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 0), 1)
        cv2.putText(telemetry_panel, f"Waypoint Index (WPI): {pp_controller.wpi} / {pp_controller.N}", (10, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)
        cv2.putText(telemetry_panel, f"Cross-Track Error (e_ct): {pp_controller.ect:+.3f}m", (10, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 255), 1)
        cv2.putText(telemetry_panel, f"Physical Wheel Sync: ACTIVE (Throttle: {args.physical_throttle})", (10, 175),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 0), 1)

        # รวมภาพ LiDAR Map (400x400) และ Telemetry Panel (400x200) เข้าด้วยกันเป็นภาพเดียว (400x600)
        composite_map = np.vstack([display_map, telemetry_panel])

        if probe.connected:
            probe.send(name="LiDAR Map", imageData=composite_map)

        time.sleep(0.033)

except KeyboardInterrupt:
    print("\nStopping Physical LiDAR & SDCSRoadMap Controller...")
finally:
    # หยุดรถทั้งระบบเพื่อความปลอดภัย
    if virtual_connected:
        try:
            virtualCar.set_velocity_and_request_state(0, 0, False, False, False, True, False)
        except Exception:
            pass
    myCar.read_write_std(0.0, 0.0, np.zeros(16, dtype=np.int8))
    myCar.terminate()
    myLidar.terminate()
    probe.terminate()
    print("All Hardware & Virtual Controllers Stopped Safely.")
