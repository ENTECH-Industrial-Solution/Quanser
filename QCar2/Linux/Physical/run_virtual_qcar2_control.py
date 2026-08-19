import time
import sys

# นำเข้าคลังไลบรารี QVL และ keyboard
try:
    import keyboard
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารีที่จำเป็น กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QCar2 Virtual Teleoperation (Control Only)
# สคริปต์สำหรับการบังคับและควบคุมรถ QCar2 ใน QLabs (ไม่มีหน้าต่างกล้อง)
# ==============================================================================

def main():
    print("==================================================")
    print("   QCar2 Virtual Teleoperation (Control Only)     ")
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

    # ตำแหน่งเริ่มต้นบนแมพ Cityscape
    start_location = [17.3, 11, 0.005]  # [X, Y, Z]
    start_rotation = [0, 0, 180]        # Roll, Pitch, Yaw (องศา)
    
    spawn_status = myCar.spawn_id_degrees(
        actorNumber=car_id,
        location=start_location,
        rotation=start_rotation,
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )

    if spawn_status == 0:
        print(f"✓ Spawn รถ QCar2 (Actor ID: {car_id}) ขึ้นในฉากสำเร็จ")
    elif spawn_status == 2:
        print(f"i รถ QCar2 (Actor ID: {car_id}) มีอยู่ในฉากแล้ว - เชื่อมต่อกับคันเดิม")
    else:
        print(f"i สถานะการ Spawn: {spawn_status} (ใช้รถเดิมในฉาก)")

    # 3. ตั้งค่าพารามิเตอร์การขับขี่
    DRIVE_SPEED = 4.0      # ความเร็วเดินหน้าปกติ (m/s)
    TURBO_SPEED = 7.5      # ความเร็วเทอร์โบ (m/s)
    REVERSE_SPEED = -3.0   # ความเร็วถอยหลัง (m/s)
    STEER_ANGLE = 30.0     # มุมเลี้ยวซ้าย/ขวา (องศา)

    headlights = False     # ไฟหน้า
    h_key_pressed = False
    r_key_pressed = False

    print("\n--------------------------------------------------")
    print("🎮 คำสั่งควบคุมคีย์บอร์ด (สามารถกดพร้อมกัน W+A / W+D ได้):")
    print("   [ W ]          : เดินหน้า")
    print("   [ Shift + W ]  : เดินหน้าเร็วแบบ Turbo")
    print("   [ S ]          : ถอยหลัง")
    print("   [ A ]          : เลี้ยวซ้าย")
    print("   [ D ]          : เลี้ยวขวา")
    print("   [ SPACE ]      : เบรกหยุดรถทันที")
    print("   [ H ]          : เปิด/ปิด ไฟหน้า")
    print("   [ R ]          : รีเซ็ตตำแหน่งรถกลับจุดเริ่มต้น")
    print("   [ Q ] หรือ [ ESC ] : ออกจากโปรแกรม")
    print("--------------------------------------------------\n")
    print("ระบบพร้อมทำงาน กำลังรับสัญญาณควบคุม...\n")

    loop_rate = 0.02  # 50 Hz (20ms ต่อรอบ เพื่อความลื่นไหลสูงสุด)
    last_print_time = time.time()
    
    try:
        while True:
            t_start = time.time()

            speed = 0.0
            steering_deg = 0.0
            left_signal = False
            right_signal = False

            # เช็คการเลี้ยว (A / D)
            if keyboard.is_pressed('a') or keyboard.is_pressed('A'):
                steering_deg = -STEER_ANGLE
                left_signal = True
            elif keyboard.is_pressed('d') or keyboard.is_pressed('D'):
                steering_deg = STEER_ANGLE
                right_signal = True

            # เช็คการเดินหน้า / ถอยหลัง (W / S / Shift / Space)
            if keyboard.is_pressed('space'):
                speed = 0.0
                steering_deg = 0.0
            elif keyboard.is_pressed('w') or keyboard.is_pressed('W'):
                if keyboard.is_pressed('shift'):
                    speed = TURBO_SPEED
                else:
                    speed = DRIVE_SPEED
            elif keyboard.is_pressed('s') or keyboard.is_pressed('S'):
                speed = REVERSE_SPEED

            # เช็คปุ่มพิเศษ (H - ไฟหน้า)
            if keyboard.is_pressed('h') or keyboard.is_pressed('H'):
                if not h_key_pressed:
                    headlights = not headlights
                    print(f"[HEADLIGHTS] {'ON' if headlights else 'OFF'}")
                    h_key_pressed = True
            else:
                h_key_pressed = False

            # เช็คปุ่มพิเศษ (R - รีเซ็ต)
            if keyboard.is_pressed('r') or keyboard.is_pressed('R'):
                if not r_key_pressed:
                    print("[RESET] รีเซ็ตตำแหน่งรถกลับจุดเริ่มต้น...")
                    speed = 0.0
                    steering_deg = 0.0
                    myCar.set_transform_and_request_state_degrees(
                        location=start_location,
                        rotation=start_rotation,
                        enableDynamics=True,
                        headlights=headlights,
                        leftTurnSignal=False,
                        rightTurnSignal=False,
                        brakeSignal=True,
                        reverseSignal=False
                    )
                    r_key_pressed = True
            else:
                r_key_pressed = False

            # เช็คปุ่มออกโปรแกรม (Q / ESC)
            if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                print("\nกำลังปิดโปรแกรม...")
                break

            # ส่งคำสั่งควบคุมไปยังตัวรถ QCar2 ใน QLabs
            brake_light = (speed == 0.0)
            reverse_signal = (speed < 0.0)

            status, current_loc, current_rot, front_hit, rear_hit = myCar.set_velocity_and_request_state_degrees(
                forward=float(speed),
                turn=float(steering_deg),
                headlights=headlights,
                leftTurnSignal=left_signal,
                rightTurnSignal=right_signal,
                brakeSignal=brake_light,
                reverseSignal=reverse_signal
            )

            # แสดงผลสถานะบน Terminal ทุกๆ 0.2 วินาที
            if time.time() - last_print_time > 0.2:
                mode_str = "TURBO" if speed >= TURBO_SPEED else ("FORWARD" if speed > 0 else ("REVERSE" if speed < 0 else "STOPPED"))
                print(f"\r[QCar2 Control] Speed: {speed:4.1f} m/s | Steer: {steering_deg:5.1f} deg | Mode: {mode_str:<7} ", end="", flush=True)
                last_print_time = time.time()

            # ควบคุมจังหวะ Loop ไม่ให้โหลด CPU
            t_elapsed = time.time() - t_start
            if t_elapsed < loop_rate:
                time.sleep(loop_rate - t_elapsed)

    except KeyboardInterrupt:
        print("\nหยุดการทำงานโดยผู้ใช้ (Ctrl+C)")
    finally:
        myCar.set_velocity_and_request_state_degrees(0, 0, False, False, False, True, False)
        print("\n✓ หยุดรถและปิดโปรแกรมเรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
