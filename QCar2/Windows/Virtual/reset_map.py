import time
import sys

# นำเข้าคลังไลบรารี QVL ของ Quanser
try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.qcar2 import QLabsQCar2
    from qvl.free_camera import QLabsFreeCamera
    from qvl.environment_outdoors import QLabsEnvironmentOutdoors
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QCar2 Map Reset Script
# สคริปต์สำหรับ Reset Map ใน QLabs เพื่อให้รถ QCar2 กลับไปจุดเริ่มต้นและวิ่งต่อได้
# ==============================================================================

def reset_map():
    print("==================================================")
    print("         QCar2 Map Reset (Virtual)                ")
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

    # 2. ลบ Actor ที่เคย Spawn ทั้งหมด (Reset Scene)
    print("-> กำลังลบวัตถุที่เคย Spawn ไว้ทั้งหมด (Reset Scene)...")
    qlabs.destroy_all_spawned_actors()
    time.sleep(1.0)

    # 3. ตั้งค่าสภาพแวดล้อม
    print("-> กำลังตั้งค่าสภาพแวดล้อม...")
    env = QLabsEnvironmentOutdoors(qlabs)
    env.set_time_of_day(8.0)
    env.set_outdoor_lighting(True)
    env.set_weather_preset(0)  # 0 = Clear Sky

    # 4. Spawn รถ QCar2 ใหม่ที่ตำแหน่งเริ่มต้น
    car_id = 1
    start_location = [17.3, 11, 0.005]
    start_rotation = [0, 0, 180]

    print(f"-> กำลัง Spawn รถ QCar2 (Actor ID: {car_id}) ที่ตำแหน่งเริ่มต้น {start_location}...")
    myCar = QLabsQCar2(qlabs)
    myCar.spawn_id_degrees(
        actorNumber=car_id,
        location=start_location,
        rotation=start_rotation,
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )

    # ตั้งค่าสีไฟ LED สีเขียว
    myCar.set_led_strip_uniform(color=[0, 1, 0], waitForConfirmation=False)

    # 5. Spawn กล้องมุมมองอิสระ
    print("-> กำลัง Spawn กล้องมุมมองอิสระ (Free Camera)...")
    camera = QLabsFreeCamera(qlabs)
    camera.spawn_id_degrees(
        actorNumber=1,
        location=[25.0, 11.0, 6.0],
        rotation=[0, 20, 180],
        waitForConfirmation=True
    )

    print("\n==================================================")
    print("✓ Reset Map สำเร็จ! รถ QCar2 พร้อมวิ่งต่อแล้ว")
    print("==================================================")
    print("  สามารถรันสคริปต์ควบคุม (controller) หรือกล้อง (camera) ต่อได้เลยครับ")
    print("  หรือดับเบิลคลิก Start_demo.bat เพื่อเริ่ม demo ใหม่ทั้งหมด")


if __name__ == "__main__":
    reset_map()
