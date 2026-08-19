import time
import sys
import math

# ==============================================================================
# QLabs Environment Setup & Comprehensive Actor Spawn Guide
# คู่มือการปรับแต่งฉากจำลอง (Environment Setup) และการ Spawn วัตถุทุกชนิดใน QLabs
# ==============================================================================

# นำเข้าคลังไลบรารี QVL ทุกหมวดหมู่สำหรับการตั้งค่าและ Spawn วัตถุ

try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.free_camera import QLabsFreeCamera
    from qvl.qcar2 import QLabsQCar2
    from qvl.qcar import QLabsQCar
    from qvl.qbot3 import QLabsQBot3
    from qvl.qbot_platform import QLabsQBotPlatform
    from qvl.qdrone2 import QLabsQDrone2
    from qvl.qarm import QLabsQArm
    from qvl.basic_shape import QLabsBasicShape
    from qvl.environment_outdoors import QLabsEnvironmentOutdoors
    from qvl.traffic_light import QLabsTrafficLight
    from qvl.stop_sign import QLabsStopSign
    from qvl.yield_sign import QLabsYieldSign
    from qvl.roundabout_sign import QLabsRoundaboutSign
    from qvl.crosswalk import QLabsCrosswalk
    from qvl.traffic_cone import QLabsTrafficCone
    from qvl.spline_line import QLabsSplineLine
    from qvl.person import QLabsPerson
    from qvl.animal import QLabsAnimal
    from qvl.walls import QLabsWalls
    from qvl.widget import QLabsWidget
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

"""
================================================================================
📌 คู่มือสรุป: วัตถุและ Actor ทั้งหมดที่สามารถ Spawn ได้ใน Quanser Interactive Labs (QLabs)
================================================================================

[ หมวดที่ 1: ยานพาหนะและหุ่นยนต์ (Vehicles & Robots) ]
  1. QLabsQCar2         : รถยนต์จำลอง QCar 2 (รุ่นล่าสุด)
  2. QLabsQCar          : รถยนต์จำลอง QCar (รุ่นแรก)
  3. QLabsQBot3         : หุ่นยนต์ฐานล้อเคลื่อนที่ QBot 3
  4. QLabsQBotPlatform  : หุ่นยนต์ฐานล้อ QBot Platform
  5. QLabsQDrone2       : โดรนจำลอง QDrone 2 (Quadrotor)
  6. QLabsQArm          : แขนกลหุ่นยนต์อุตสาหกรรม QArm
  7. QLabsQBot2e        : หุ่นยนต์ฐานล้อ QBot 2e

[ หมวดที่ 2: อุปกรณ์จราจรและโครงสร้างถนน (Traffic & Road Infrastructure) ]
  1. QLabsTrafficLight  : ไฟสัญญาณจราจร (สลับสี แดง/เหลือง/เขียว ได้)
  2. QLabsStopSign      : ป้ายหยุด (Stop Sign)
  3. QLabsYieldSign     : ป้ายให้ทาง (Yield Sign)
  4. QLabsRoundaboutSign: ป้ายวงเวียน (Roundabout Sign)
  5. QLabsCrosswalk     : ทางข้าม / ทางลายพาดกว้าง (Crosswalk)
  6. QLabsTrafficCone   : กรวยจราจร (Traffic Cone)
  7. QLabsSplineLine    : เส้นจราจร / ขอบทางแบบปรับรูปทรงได้ (Spline Line)
  8. QLabsWalls         : กำแพง / รั้วกั้นพื้นที่ (Walls)

[ หมวดที่ 3: วัตถุเรขาคณิตและก้อนฟิสิกส์ (Basic Shapes & Rigid Bodies) ]
  1. QLabsBasicShape    : รูปทรงเรขาคณิต (ปรับขนาด สี วัสดุ ได้):
     - Config 0: ลูกบาศก์ (Cube)
     - Config 1: ทรงกระบอก (Cylinder)
     - Config 2: ทรงกลม (Sphere)
     - Config 3: กรวย (Cone)
     - Config 4: ทรงแหวน (Torus)
  2. QLabsWidget        : วัตถุฟิสิกส์หล่นตามแรงโน้มถ่วง (เช่น กล่องไม้, ลูกบอล, ถังน้ำมัน)

[ หมวดที่ 4: สิ่งแวดล้อม สภาพอากาศ และแสงแดด (Environment, Weather & Lighting) ]
  1. QLabsEnvironmentOutdoors : ปรับแต่งสภาพแวดล้อมภายนอก:
     - set_time_of_day(time)        : ปรับเวลาในรอบวัน (0.0 ถึง 24.0 นาฬิกา)
     - set_weather_preset(preset)   : เลือกสภาพอากาศ (0: Clear แดดจัด, 1: Cloudy เมฆมาก, 2: Rainy ฝนตก, 3: Foggy หมอกลง, 4: Snowy หิมะ)
     - set_outdoor_lighting(enable) : เปิด/ปิด แสงอาทิตย์และแสงบรรยากาศ

[ หมวดที่ 5: ตัวละคร มนุษย์ และสัตว์ (Pedestrians & Animals) ]
  1. QLabsPerson        : คนเดินถนน (กำหนดท่าทาง เดิน/ยืน/วิ่ง ไปยังพิกัดที่ต้องการได้)
  2. QLabsAnimal        : สัตว์จำลอง

[ หมวดที่ 6: กล้องอิสระและระบบอ้างอิง (Free Camera & Frames) ]
  1. QLabsFreeCamera    : กล้องมุมมองอิสระ ปรับตำแหน่ง พิกัด และซูมมุมมองได้ตามต้องการ

================================================================================
🛠️ สรุปขั้นตอนและวิธีการ Spawn วัตถุ (Step-by-Step Spawn Workflow)
================================================================================

1. เชื่อมต่อกับ QLabs Server:
   qlabs = QuanserInteractiveLabs()
   qlabs.open("localhost")

2. ลบ วัตถุเก่าทั้งหมดเพื่อรีเซ็ตฉาก (ถ้าต้องการ):
   qlabs.destroy_all_spawned_actors()

3. วิธีการ Spawn วัตถุด้วยพิกัดองศา (Degrees):
   actor = QLabsQCar2(qlabs)
   actor.spawn_id_degrees(
       actorNumber=1,                  # ID ประจำตัววัตถุ (ต้องไม่ซ้ำกันในคลาสเดียวกัน)
       location=[X, Y, Z],              # พิกัดตำแหน่งในหน่วยเมตร [X, Y, Z]
       rotation=[Roll, Pitch, Yaw],     # มุมหมุนเป็นองศา [Roll, Pitch, Yaw]
       scale=[ScaleX, ScaleY, ScaleZ],  # ขนาดขยาย (1.0 คือขนาดปกติ)
       configuration=0,                 # รูปแบบย่อยของวัตถุ
       waitForConfirmation=True        # รอการตอบรับจาก QLabs
   )

4. วิธีการผูกวัตถุลูกเข้ากับวัตถุแม่ (Parenting):
   child_object.spawn_id_and_parent_with_relative_transform(
       actorNumber=2,
       location=[RelX, RelY, RelZ],     # ตำแหน่งสัมพัทธ์เทียบกับวัตถุแม่
       rotation=[RelRoll, RelPitch, RelYaw],
       scale=[Sx, Sy, Sz],
       configuration=0,
       parentClassID=QLabsQCar2.ID_QCAR,
       parentActorNumber=1,
       waitForConfirmation=True
   )
================================================================================
"""

def setup_demo_environment(qlabs):
    print("\n--------------------------------------------------")
    print("🛠️  เริ่มกระบวนการจัดเตรียมสภาพแวดล้อม (Environment Setup)...")
    print("--------------------------------------------------")

    # 1. รีเซ็ตและลบ Actor ที่เคย Spawn ทั้งหมดในฉากออกก่อน
    print("-> กำลังลบวัตถุที่เคย Spawn ไว้ทั้งหมด (Reset Scene)...")
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)

    # 2. ปรับแต่งสภาพแวดล้อมภายนอก (เวลา, สภาพอากาศ, แสงแดด)
    print("-> กำลังตั้งค่าสภาพแวดล้อม สภาพอากาศ และเวลา (Environment Outdoors)...")
    env = QLabsEnvironmentOutdoors(qlabs)
    env.set_time_of_day(8.0)           # ตั้งเวลาบ่าย 2 โมง (14:00 น.)
    env.set_outdoor_lighting(True)      # เปิดแสงอาทิตย์
    env.set_weather_preset(0)           # 0 = Clear Sky (ท้องฟ้าสดใส)

    # 3. Spawn ตัวรถ QCar2 หลัก (Actor ID = 1) - รถสีเขียว
    print("-> กำลัง Spawn รถ QCar2 หลัก (Actor #1)...")
    car1 = QLabsQCar2(qlabs)
    car1.spawn_id_degrees(
        actorNumber=1,
        location=[17.3, 11, 0.005],     # พิกัด [X, Y, Z]
        rotation=[0, 0, 180],           # พิกัดองศา [Roll, Pitch, Yaw]
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )
    car1.set_led_strip_uniform(color=[0, 1, 0]) # ตั้งสีไฟ LED สีเขียว

    # 4. Spawn รถ QCar2 คันที่ 2 (Actor ID = 2) - รถสีเหลืองสำหรับทดสอบการหลบหลีก
    print("-> กำลัง Spawn รถ QCar2 สิ่งกีดขวาง (Actor #2)...")
    car2 = QLabsQCar2(qlabs)
    car2.spawn_id_degrees(
        actorNumber=2,
        location=[12.0, 11.0, 0.005],   # จอดจ่ออยู่ด้านหน้าของรถคันที่ 1
        rotation=[0, 0, 180],
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )
    car2.set_led_strip_uniform(color=[1, 1, 0]) # สีเหลือง

    # 5. Spawn สัญญาณไฟจราจร (Traffic Light)
    print("-> กำลัง Spawn สัญญาณไฟจราจร (Traffic Light)...")
    t_light = QLabsTrafficLight(qlabs)
    t_light.spawn_id_degrees(
        actorNumber=1,
        location=[6.0, 14.0, 0.0],
        rotation=[0, 0, 90],
        scale=[1, 1, 1],
        configuration=0, # เสาไฟจราจรแบบมาตรฐาน
        waitForConfirmation=True
    )
    t_light.set_state(QLabsTrafficLight.STATE_GREEN) # เปิดไฟเขียว

    # 6. Spawn ป้ายหยุด (Stop Sign)
    print("-> กำลัง Spawn ป้ายหยุด (Stop Sign)...")
    stop_sign = QLabsStopSign(qlabs)
    stop_sign.spawn_id_degrees(
        actorNumber=1,
        location=[20.0, 8.0, 0.0],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        waitForConfirmation=True
    )

    # 7. Spawn กรวยจราจร (Traffic Cones)
    print("-> กำลัง Spawn กรวยจราจร (Traffic Cones)...")
    cone_positions = [
        [15.0, 12.0, 0.0],
        [15.0, 10.0, 0.0],
        [10.0, 12.0, 0.0],
    ]
    for idx, pos in enumerate(cone_positions):
        cone = QLabsTrafficCone(qlabs)
        cone.spawn_id_degrees(
            actorNumber=idx + 1,
            location=pos,
            rotation=[0, 0, 0],
            scale=[1, 1, 1],
            waitForConfirmation=True
        )

    # 8. Spawn คนเดินถนน (Pedestrian Person)
    print("-> กำลัง Spawn คนเดินถนน (Pedestrian)...")
    person = QLabsPerson(qlabs)
    person.spawn_id_degrees(
        actorNumber=1,
        location=[8.0, 13.0, 0.0],
        rotation=[0, 0, -90],
        scale=[1, 1, 1],
        configuration=0, # ชายแต่งตัวลำลอง
        waitForConfirmation=True
    )

    # 9. Spawn กล้องมุมมองอิสระ (Free Camera) เพื่อจัดมุมมองภาพรวม
    print("-> กำลัง Spawn กล้องมุมมองอิสระ (Free Camera)...")
    camera = QLabsFreeCamera(qlabs)
    camera.spawn_id_degrees(
        actorNumber=1,
        location=[25.0, 11.0, 6.0],     # พิกัดกล้องสูงมองลงมา
        rotation=[0, 20, 180],          # ก้มกล้องมองไปทางตัวรถ
        waitForConfirmation=True
    )

    print("\n--------------------------------------------------")
    print("✓ จัดเตรียมสภาพแวดล้อมและ Spawn วัตถุเรียบร้อยแล้ว!")
    print("--------------------------------------------------\n")


def main():
    print("==================================================")
    print("    QCar2 Virtual Environment Setup Manager       ")
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
        input("กด Enter เพื่อปิด...")
        return

    # เรียกใช้งานฟังก์ชั่นสร้างสภาพแวดล้อม
    setup_demo_environment(qlabs)

    print("💡 สามารถเปิดใช้งานสคริปต์กล้อง LiDAR หรือตัวควบคุมขับขี่ต่อได้ทันที")

if __name__ == "__main__":
    main()
