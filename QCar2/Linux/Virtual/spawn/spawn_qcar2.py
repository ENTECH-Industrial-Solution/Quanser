import time
import sys

# นำเข้าคลังไลบรารี QVL ของ Quanser
try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QCar2 Virtual Entity Spawner
# สคริปต์สำหรับการ Spawn และตั้งค่าตำแหน่งเริ่มต้นของรถ QCar2 ในฉาก QLabs
# ==============================================================================

def main():
    print("==================================================")
    print("         QCar2 Virtual Entity Spawner             ")
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

    # 2. ตั้งค่าพิกัดเริ่มต้นในการ Spawn (แมพ Cityscape)
    car_id = 1
    myCar = QLabsQCar2(qlabs)
    
    start_location = [17.3, 11, 0.005]  # [X, Y, Z]
    start_rotation = [0, 0, 180]        # Roll, Pitch, Yaw (องศา)

    print(f"กำลัง Spawn รถ QCar2 (Actor ID: {car_id}) ไปยังตำแหน่ง {start_location}...")

    # สั่ง Spawn ตัวรถขึ้นในฉาก
    spawn_status = myCar.spawn_id_degrees(
        actorNumber=car_id,
        location=start_location,
        rotation=start_rotation,
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )

    if spawn_status == 0:
        print(f"✓ Spawn รถ QCar2 (Actor ID: {car_id}) ขึ้นในฉากสำเร็จ!")
    elif spawn_status == 2:
        print(f"i รถ QCar2 (Actor ID: {car_id}) มีอยู่ในฉากแล้ว - ทำการรีเซ็ตตำแหน่งไปยังจุดเริ่มต้น")
        myCar.actorNumber = car_id
        myCar.set_transform_and_request_state_degrees(
            location=start_location,
            rotation=start_rotation,
            enableDynamics=True,
            headlights=False,
            leftTurnSignal=False,
            rightTurnSignal=False,
            brakeSignal=True,
            reverseSignal=False
        )
        print(f"✓ รีเซ็ตตำแหน่ง QCar2 สำเร็จ!")
    else:
        print(f"⚠️ สถานะการ Spawn: {spawn_status}")

    # 3. ตั้งค่าสีไฟ LED เริ่มต้น (สีเขียว)
    myCar.actorNumber = car_id
    myCar.set_led_strip_uniform(color=[0, 1, 0], waitForConfirmation=False)
    
    print("--------------------------------------------------")
    print("✓ ดำเนินการ Spawn/Reset QCar2 เรียบร้อยแล้ว")
    print("  สามารถรันสคริปต์ควบคุม (run_virtual_qcar2_control.py)")
    print("  หรือสคริปต์กล้อง (view_virtual_qcar2_camera.py) ต่อได้เลยครับ")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
