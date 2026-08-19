import time
import sys
import math
import os
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# นำเข้าคลังไลบรารี QVL
try:
    from qvl.qlabs import QuanserInteractiveLabs
    from qvl.walls import QLabsWalls
    from qvl.basic_shape import QLabsBasicShape
    from qvl.qcar2 import QLabsQCar2
except ImportError:
    print("Error: ไม่พบไลบรารี QVL (qvl) กรุณาตรวจสอบการตั้งค่า Python environment")
    sys.exit(1)

# ==============================================================================
# QLabs Custom Wall Spawner & Live Auto-Reload Manager (set_wall.py)
# สคริปต์โหลดกำแพงแบบ Custom พร้อมโหมด Auto-Reload อัปเดตกำแพงตามไฟล์ JSON แบบ Real-time
# ==============================================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wall_config.json")

DEFAULT_CONFIG = {
    "description": "QCar2 QLabs Custom Wall Configuration File",
    "version": "1.0",
    "auto_reset_scene": False,
    "walls": [
        {
            "name": "Arena Box Enclosure",
            "type": "enclosure",
            "id": 200,
            "center": [12.0, 11.0],
            "width": 12.0,
            "length": 20.0,
            "height": 0.8,
            "enabled": True
        },
        {
            "name": "Corner Curved Wall Arc",
            "type": "curved",
            "id": 400,
            "center": [10.0, 8.0],
            "radius": 3.5,
            "start_angle": 0.0,
            "end_angle": 90.0,
            "num_segments": 10,
            "height": 0.8,
            "thickness": 0.3,
            "color": [0.2, 0.7, 0.9],
            "enabled": True
        },
        {
            "name": "Roundabout Circular Wall",
            "type": "circular",
            "id": 500,
            "center": [6.0, 11.0],
            "radius": 2.5,
            "num_segments": 16,
            "height": 0.8,
            "thickness": 0.3,
            "color": [0.2, 0.9, 0.4],
            "enabled": True
        },
        {
            "name": "Front Obstacle Wall 1",
            "type": "straight",
            "id": 1,
            "location": [14.0, 11.0, 0.0],
            "rotation": [0.0, 0.0, 90.0],
            "scale": [3.5, 0.4, 1.0],
            "color": [1.0, 0.5, 0.0],
            "enabled": True
        },
        {
            "name": "Side Obstacle Wall 2",
            "type": "straight",
            "id": 2,
            "location": [8.0, 11.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [3.0, 0.4, 1.0],
            "color": [0.9, 0.1, 0.1],
            "enabled": True
        }
    ]
}


def load_wall_config(config_path=CONFIG_FILE):
    """ อ่านไฟล์การตั้งค่ากำแพง wall_config.json """
    if not os.path.exists(config_path):
        print(f"📄 ไม่พบไฟล์คอนฟิก กำลังสร้างไฟล์ตั้งต้น: {config_path}")
        save_wall_config(DEFAULT_CONFIG, config_path)
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"⚠️ อ่านไฟล์คอนฟิกขัดข้อง ({e}) กำลังใช้ค่าเริ่มต้น...")
        return DEFAULT_CONFIG


def save_wall_config(config_data, config_path=CONFIG_FILE):
    """ บันทึกการตั้งค่ากำแพงลงไฟล์ wall_config.json """
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ บันทึกไฟล์คอนฟิกไม่สำเร็จ: {e}")
        return False


def spawn_single_wall(qlabs, wall_id, location, rotation=[0, 0, 0], scale=[3.5, 0.4, 1.0], color=[1.0, 0.5, 0.0], use_basic_shape=True):
    """ ฟังก์ชันสำหรับ Spawn กำแพงตรงเดี่ยว (Single Straight Wall) """
    loc_z = location[2] if len(location) > 2 and location[2] > 0 else (scale[2] / 2.0)
    adjusted_loc = [location[0], location[1], loc_z]

    if use_basic_shape:
        wall = QLabsBasicShape(qlabs)
        wall.spawn_id_degrees(
            actorNumber=wall_id,
            location=adjusted_loc,
            rotation=rotation,
            scale=scale,
            configuration=QLabsBasicShape.SHAPE_CUBE,
            waitForConfirmation=True
        )
        wall.set_material_properties(color=color, roughness=0.3, metallic=False)
        wall.set_enable_collisions(True)
    else:
        wall = QLabsWalls(qlabs)
        wall.spawn_id_degrees(
            actorNumber=wall_id,
            location=adjusted_loc,
            rotation=rotation,
            scale=scale,
            configuration=QLabsWalls.WALL_FOAM_BOARD,
            waitForConfirmation=True
        )

    print(f"  [Single Wall #{wall_id}] Spawned at X={adjusted_loc[0]:.1f}, Y={adjusted_loc[1]:.1f}, Z={adjusted_loc[2]:.1f} | Length={scale[0]}m")
    return wall


def spawn_curved_wall(qlabs, start_id=400, center=[12.0, 11.0], radius=4.0, start_angle_deg=0.0, end_angle_deg=90.0, num_segments=12, wall_height=0.8, wall_thickness=0.3, color=[0.2, 0.7, 0.9]):
    """ ฟังก์ชันสร้างกำแพงส่วนโค้ง (Curved Wall Arc) """
    print(f"\n🌀 กำลังสร้างกำแพงโค้ง (Curved Wall #{start_id}) รัศมี {radius}m | มุม {start_angle_deg}° ถึง {end_angle_deg}°...")

    angle_step_deg = (end_angle_deg - start_angle_deg) / max(1, num_segments - 1)
    angle_step_rad = math.radians(angle_step_deg)
    segment_length = 2 * radius * math.sin(angle_step_rad / 2.0) * 1.06

    for i in range(num_segments):
        current_angle_deg = start_angle_deg + i * angle_step_deg
        current_angle_rad = math.radians(current_angle_deg)

        x = center[0] + radius * math.cos(current_angle_rad)
        y = center[1] + radius * math.sin(current_angle_rad)
        z = wall_height / 2.0

        yaw_deg = current_angle_deg + 90.0

        shape = QLabsBasicShape(qlabs)
        shape.spawn_id_degrees(
            actorNumber=start_id + i,
            location=[x, y, z],
            rotation=[0, 0, yaw_deg],
            scale=[segment_length, wall_thickness, wall_height],
            configuration=QLabsBasicShape.SHAPE_CUBE,
            waitForConfirmation=False
        )
        shape.set_material_properties(color=color, roughness=0.3, metallic=False)
        shape.set_enable_collisions(True)

    print(f"✓ สร้างกำแพงโค้งสำเร็จ! ({num_segments} ชิ้นส่วน)")


def build_wall_enclosure(qlabs, start_id=100, center_x=12.0, center_y=11.0, width=12.0, length=20.0, wall_height=0.8):
    """ ฟังก์ชันสร้างกำแพงล้อมรอบสนาม (Perimeter Box Enclosure) 4 ทิศทาง """
    print(f"\n🧱 กำลังสร้างกำแพงล้อมรอบสนาม (Center: [{center_x}, {center_y}], ขนาด: {length}x{width} เมตร)...")

    half_w = width / 2.0
    half_l = length / 2.0
    current_id = start_id

    # North
    spawn_single_wall(qlabs, current_id, [center_x, center_y + half_w, wall_height / 2.0], [0, 0, 0], [length, 0.4, wall_height], [0.9, 0.3, 0.1])
    current_id += 1
    # South
    spawn_single_wall(qlabs, current_id, [center_x, center_y - half_w, wall_height / 2.0], [0, 0, 0], [length, 0.4, wall_height], [0.9, 0.3, 0.1])
    current_id += 1
    # East
    spawn_single_wall(qlabs, current_id, [center_x + half_l, center_y, wall_height / 2.0], [0, 0, 90], [width, 0.4, wall_height], [0.2, 0.6, 0.9])
    current_id += 1
    # West
    spawn_single_wall(qlabs, current_id, [center_x - half_l, center_y, wall_height / 2.0], [0, 0, 90], [width, 0.4, wall_height], [0.2, 0.6, 0.9])

    print("✓ สร้างกำแพงล้อมรอบสนามสำเร็จ!")


def spawn_walls_from_config(qlabs, config_data):
    """ อ่านการตั้งค่าจาก JSON แล้ว Spawn กำแพงทุกรายการเข้าสู่ QLabs """
    walls_list = config_data.get("walls", [])
    if not walls_list:
        print("⚠️ ไม่พบรายการกำแพงในไฟล์คอนฟิก")
        return

    print(f"\n🧱 เริ่มสร้างกำแพงจากไฟล์คอนฟิก (รวม {len(walls_list)} รายการ)...")

    for item in walls_list:
        if not item.get("enabled", True):
            print(f"  [Skipped] {item.get('name', 'Wall')} (Disabled)")
            continue

        w_type = item.get("type", "straight").lower()
        w_id = item.get("id", 1)
        w_name = item.get("name", f"Wall #{w_id}")

        print(f"\n-> Creating [{w_name}] (Type: {w_type})...")

        if w_type == "straight":
            loc = item.get("location", [0.0, 0.0, 0.0])
            rot = item.get("rotation", [0.0, 0.0, 0.0])
            scale = item.get("scale", [3.0, 0.4, 1.0])
            color = item.get("color", [1.0, 0.5, 0.0])
            spawn_single_wall(qlabs, w_id, loc, rot, scale, color)

        elif w_type == "curved":
            center = item.get("center", [10.0, 8.0])
            radius = item.get("radius", 4.0)
            start_ang = item.get("start_angle", 0.0)
            end_ang = item.get("end_angle", 90.0)
            segments = item.get("num_segments", 12)
            h = item.get("height", 0.8)
            th = item.get("thickness", 0.3)
            color = item.get("color", [0.2, 0.7, 0.9])
            spawn_curved_wall(qlabs, w_id, center, radius, start_ang, end_ang, segments, h, th, color)

        elif w_type == "circular":
            center = item.get("center", [6.0, 11.0])
            radius = item.get("radius", 2.5)
            segments = item.get("num_segments", 16)
            h = item.get("height", 0.8)
            th = item.get("thickness", 0.3)
            color = item.get("color", [0.2, 0.9, 0.4])
            spawn_curved_wall(qlabs, w_id, center, radius, 0.0, 360.0, segments, h, th, color)

        elif w_type == "enclosure":
            center = item.get("center", [12.0, 11.0])
            w = item.get("width", 12.0)
            l = item.get("length", 20.0)
            h = item.get("height", 0.8)
            build_wall_enclosure(qlabs, w_id, center[0], center[1], w, l, h)


def watch_and_auto_reload(qlabs, config_path=CONFIG_FILE):
    """ โหมดเฝ้ามองไฟล์แบบต่อเนื่อง (Live Auto-Reload): อัปเดต QLabs ทันทีเมื่อบันทึกไฟล์ JSON """
    print("\n--------------------------------------------------------------")
    print("👀 เปิดใช้งานโหมด Live Auto-Reload (File Watcher Mode)...")
    print(f"   -> ไฟล์คอนฟิก: {config_path}")
    print("   -> เมื่อคุณปรับแก้และบันทึกไฟล์ (Save) สคริปต์จะอัปเดตกำแพงทันที!")
    print("   -> กด Ctrl+C ในหน้าต่างนี้เพื่อหยุดการทำงาน")
    print("--------------------------------------------------------------\n")

    last_mtime = 0

    try:
        while True:
            if os.path.exists(config_path):
                current_mtime = os.path.getmtime(config_path)
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    time_str = time.strftime('%H:%M:%S')
                    print(f"\n⚡ [{time_str}] ตรวจพบการบันทึกไฟล์ wall_config.json! กำลังอัปเดตกำแพง...")

                    config_data = load_wall_config(config_path)

                    qlabs.destroy_all_spawned_actors()
                    time.sleep(0.3)

                    car1 = QLabsQCar2(qlabs)
                    car1.spawn_id_degrees(
                        actorNumber=1,
                        location=[17.3, 11.0, 0.005],
                        rotation=[0, 0, 180],
                        scale=[1, 1, 1],
                        waitForConfirmation=False
                    )

                    spawn_walls_from_config(qlabs, config_data)
                    print(f"\n✓ [{time_str}] อัปเดตรูปแบบกำแพงใน QLabs เรียบร้อยแล้ว! (กำลังรอการบันทึกครั้งต่อไป...)\n")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nหยุดระบบ Auto-Reload โดยผู้ใช้ (Ctrl+C)")


def main():
    parser = argparse.ArgumentParser(description="QLabs Custom Wall Spawner & Auto-Reload Manager")
    parser.add_argument("--watch", "-w", action="store_true", help="เปิดโหมดเฝ้ามองไฟล์เพื่อ Auto-Reload เมื่อมีการกด Save")
    args = parser.parse_args()

    print("==================================================")
    print(" QLabs Custom Wall Spawner & Config Manager       ")
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

    if args.watch:
        watch_and_auto_reload(qlabs, CONFIG_FILE)
        return

    config_data = load_wall_config(CONFIG_FILE)

    if config_data.get("auto_reset_scene", False):
        print("-> กำลังรีเซ็ตลบวัตถุในฉากก่อนสปอว์นใหม่ (auto_reset_scene: true)...")
        qlabs.destroy_all_spawned_actors()
        time.sleep(0.5)

    car1 = QLabsQCar2(qlabs)
    car1.spawn_id_degrees(
        actorNumber=1,
        location=[17.3, 11.0, 0.005],
        rotation=[0, 0, 180],
        scale=[1, 1, 1],
        waitForConfirmation=False
    )

    spawn_walls_from_config(qlabs, config_data)

    print("\n--------------------------------------------------")
    print("✓ สปอว์นกำแพงแบบ Custom จาก wall_config.json เสร็จสิ้น!")
    print("💡 ปิดหน้าต่างอัตโนมัติใน 1.5 วินาที...")
    print("--------------------------------------------------\n")
    time.sleep(1.5)
    sys.exit(0)

if __name__ == "__main__":
    main()
