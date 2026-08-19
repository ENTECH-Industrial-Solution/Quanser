import time
import sys
import math

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
# QLabs Wall Spawning Manager & Perimeter Builder
# สคริปต์สำหรับการ Spawn กำแพงตรง กำแพงล้อมรอบ และกำแพงโค้ง (Curved Walls) ใน QLabs
# ==============================================================================

def spawn_single_wall(qlabs, wall_id, location, rotation=[0, 0, 0], scale=[3.0, 0.3, 1.0], color=[0.9, 0.2, 0.2], use_basic_shape=True):
    """
    ฟังก์ชันสำหรับ Spawn กำแพงตรงเดี่ยว (Single Straight Wall)
    """
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

    print(f"  [Single Straight Wall #{wall_id}] Spawned at X={adjusted_loc[0]:.1f}, Y={adjusted_loc[1]:.1f}, Z={adjusted_loc[2]:.1f} | Length={scale[0]}m, Height={scale[2]}m")
    return wall


def spawn_block_barrier(qlabs, shape_id, location, rotation=[0, 0, 0], scale=[2.0, 0.3, 1.0], color=[0.8, 0.2, 0.2]):
    """
    ฟังก์ชันสำหรับ Spawn กำแพงบล็อกเรขาคณิต (QLabsBasicShape Cube)
    """
    return spawn_single_wall(qlabs, shape_id, location, rotation, scale, color, use_basic_shape=True)


def spawn_curved_wall(qlabs, start_id=400, center=[12.0, 11.0], radius=4.0, start_angle_deg=0.0, end_angle_deg=90.0, num_segments=12, wall_height=0.8, wall_thickness=0.3, color=[0.2, 0.7, 0.9]):
    """
    ฟังก์ชันสร้างกำแพงส่วนโค้ง (Curved Wall Arc)
    """
    print(f"\n🌀 กำลังสร้างกำแพงโค้ง (Curved Wall) รัศมี {radius}m | มุม {start_angle_deg}° ถึง {end_angle_deg}°...")

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

    print(f"✓ สร้างกำแพงโค้งสำเร็จ! (รวม {num_segments} ชิ้นส่วน, IDs: #{start_id} ถึง #{start_id + num_segments - 1})")


def spawn_circular_roundabout_wall(qlabs, start_id=500, center=[12.0, 11.0], radius=3.5, num_segments=16, color=[0.3, 0.8, 0.3]):
    """
    ฟังก์ชันสร้างกำแพงวงกลมเต็มวง / วงเวียน (Circular Wall / Roundabout Barrier)
    """
    print(f"\n⭕ กำลังสร้างกำแพงวงกลม/วงเวียน (Circular Wall) รัศมี {radius}m...")
    spawn_curved_wall(
        qlabs,
        start_id=start_id,
        center=center,
        radius=radius,
        start_angle_deg=0.0,
        end_angle_deg=360.0,
        num_segments=num_segments,
        wall_height=0.8,
        wall_thickness=0.3,
        color=color
    )


def build_wall_enclosure(qlabs, start_id=100, center_x=15.0, center_y=11.0, width=10.0, length=12.0, wall_height=1.0):
    """
    ฟังก์ชันสร้างกำแพงล้อมรอบสนาม (Perimeter Box Enclosure) 4 ทิศทาง (เหนือ, ใต้, ตะวันออก, ตะวันตก)
    """
    print(f"\n🧱 กำลังสร้างกำแพงล้อมรอบสนาม (Center: [{center_x}, {center_y}], ขนาด: {length}x{width} เมตร)...")

    half_w = width / 2.0
    half_l = length / 2.0

    current_id = start_id

    # 1. กำแพงฝั่งเหนือ (North Wall)
    spawn_single_wall(
        qlabs, current_id,
        location=[center_x, center_y + half_w, wall_height / 2.0],
        rotation=[0, 0, 0],
        scale=[length, 0.3, wall_height],
        color=[0.9, 0.3, 0.1]
    )
    current_id += 1

    # 2. กำแพงฝั่งใต้ (South Wall)
    spawn_single_wall(
        qlabs, current_id,
        location=[center_x, center_y - half_w, wall_height / 2.0],
        rotation=[0, 0, 0],
        scale=[length, 0.3, wall_height],
        color=[0.9, 0.3, 0.1]
    )
    current_id += 1

    # 3. กำแพงฝั่งตะวันออก (East Wall)
    spawn_single_wall(
        qlabs, current_id,
        location=[center_x + half_l, center_y, wall_height / 2.0],
        rotation=[0, 0, 90],
        scale=[width, 0.3, wall_height],
        color=[0.2, 0.6, 0.9]
    )
    current_id += 1

    # 4. กำแพงฝั่งตะวันตก (West Wall)
    spawn_single_wall(
        qlabs, current_id,
        location=[center_x - half_l, center_y, wall_height / 2.0],
        rotation=[0, 0, 90],
        scale=[width, 0.3, wall_height],
        color=[0.2, 0.6, 0.9]
    )
    current_id += 1

    print("✓ สร้างกำแพงล้อมรอบสนามสำเร็จ!")


def main():
    print("==================================================")
    print(" QLabs Wall, Barrier & Curved Wall Spawner        ")
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

    print("\nกำลังสร้างกำแพงตรง กำแพงล้อมรอบสนาม และกำแพงโค้ง...")

    car1 = QLabsQCar2(qlabs)
    car1.spawn_id_degrees(
        actorNumber=1,
        location=[17.3, 11.0, 0.005],
        rotation=[0, 0, 180],
        scale=[1, 1, 1],
        waitForConfirmation=False
    )

    build_wall_enclosure(
        qlabs,
        start_id=200,
        center_x=12.0,
        center_y=11.0,
        width=12.0,
        length=20.0,
        wall_height=0.8
    )

    spawn_curved_wall(
        qlabs,
        start_id=400,
        center=[10.0, 8.0],
        radius=3.5,
        start_angle_deg=0.0,
        end_angle_deg=90.0,
        num_segments=10,
        wall_height=0.8,
        color=[0.2, 0.7, 0.9]
    )

    spawn_circular_roundabout_wall(
        qlabs,
        start_id=500,
        center=[6.0, 11.0],
        radius=2.5,
        num_segments=16,
        color=[0.2, 0.9, 0.4]
    )

    print("\n🧱 กำลัง Spawn กำแพงตรงเดี่ยวบนถนน (Single Straight Obstacle Walls)...")
    spawn_single_wall(qlabs, wall_id=1, location=[14.0, 11.0], rotation=[0, 0, 90], scale=[3.5, 0.4, 1.0], color=[1.0, 0.5, 0.0])
    spawn_single_wall(qlabs, wall_id=2, location=[8.0, 11.0], rotation=[0, 0, 0], scale=[3.0, 0.4, 1.0], color=[0.9, 0.1, 0.1])

    print("\n--------------------------------------------------")
    print("✓ สร้างกำแพงทั้งหมด (กำแพงตรงเดี่ยว + กำแพงโค้ง + วงเวียน) เสร็จเรียบร้อยแล้ว!")
    print("--------------------------------------------------\n")

if __name__ == "__main__":
    main()
