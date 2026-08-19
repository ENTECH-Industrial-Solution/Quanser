import sys
#sys.path.append('../libraries/')
#import numpy as np

from qvl.qlabs import QuanserInteractiveLabs
from qvl.free_camera import QLabsFreeCamera
from qvl.qcar2 import QLabsQCar2
from qvl.basic_shape import QLabsBasicShape
from qvl.environment_outdoors import QLabsEnvironmentOutdoors
from qvl.traffic_light import QLabsTrafficLight
from qvl.stop_sign import QLabsStopSign
from qvl.spline_line import QLabsSplineLine
from qvl.person import QLabsPerson
from qvl.roundabout_sign import QLabsRoundaboutSign
import time
print("\n--------------------------------")
print("Environment Setup")
print("--------------------------------")


global retry_count
retry_count=0
def try_conneting():
    global retry_count
    if retry_count>20:
        print('unable to connect')
        exit()
    try:
        assert qlabs.open("localhost")
    except:
        retry_count+=1
        time.sleep(2)
        try_conneting()

qlabs = QuanserInteractiveLabs()
print("Connecting to QLabs...")
try_conneting()
# destroy all spawned actors to reset the scene
print("Deleting current spawned actors...")
qlabs.destroy_all_spawned_actors()

print("Spawning new actors...")

if(len(sys.argv) > 1):
    if (sys.argv[1] == "UseWeather"):

        hEnvironmentOutdoors = QLabsEnvironmentOutdoors(qlabs)
        hEnvironmentOutdoors.set_time_of_day(12) #1:00pm
        hEnvironmentOutdoors.set_outdoor_lighting(False)
        hEnvironmentOutdoors.set_weather_preset(0)
        print("Weather enabled")
    else:
        print("Weather disabled")
else:
    print("Weather disabled")

# Green car
car1 = QLabsQCar2(qlabs)
car1.spawn_id_degrees(actorNumber=1, location=[17.3, 11, 0.005], rotation=[0, 0, 180], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
car1.set_led_strip_uniform(color=[0, 1, 0],waitForConfirmation=False)
circle1 = QLabsBasicShape(qlabs)
circle1.spawn_id_and_parent_with_relative_transform(actorNumber=int(1), 
                                                        location=[1.2,0,1.865], 
                                                        rotation=[0,0,0], 
                                                        scale=[0.6,0.6,.029], 
                                                        configuration=int(1), 
                                                        parentClassID=int(QLabsQCar2.ID_QCAR), 
                                                        parentActorNumber=int(car1.actorNumber), 
                                                        parentComponent=int(0), 
                                                        waitForConfirmation=True)
circle1.set_material_properties([0,1,0], roughness=0.7, metallic=False)

# Yellow car
car2 = QLabsQCar2(qlabs)
car2.spawn_id_degrees(actorNumber=2, location=[-13, -8, 0.005], rotation=[0, 0, -45], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
car2.set_led_strip_uniform(color=[1, 1, 0],waitForConfirmation=False)
circle2 = QLabsBasicShape(qlabs)
circle2.spawn_id_and_parent_with_relative_transform(actorNumber=int(2), 
                                                        location=[1.2,0,1.865], 
                                                        rotation=[0,0,0], 
                                                        scale=[0.6,0.6,.029], 
                                                        configuration=int(1), 
                                                        parentClassID=int(QLabsQCar2.ID_QCAR), 
                                                        parentActorNumber=int(car2.actorNumber), 
                                                        parentComponent=int(0), 
                                                        waitForConfirmation=True)
circle2.set_material_properties([1,1,0], roughness=0.7, metallic=False)

# Red car
car3 = QLabsQCar2(qlabs)
car3.spawn_id_degrees(actorNumber=3, location=[-18, -4, 0.005], rotation=[0, 0, -45], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
car3.set_led_strip_uniform(color=[1, 0, 0],waitForConfirmation=False)
circle3 = QLabsBasicShape(qlabs)
circle3.spawn_id_and_parent_with_relative_transform(actorNumber=int(3), 
                                                        location=[1.2,0,1.865], 
                                                        rotation=[0,0,0], 
                                                        scale=[0.6,0.6,.029], 
                                                        configuration=int(1), 
                                                        parentClassID=int(QLabsQCar2.ID_QCAR), 
                                                        parentActorNumber=int(car3.actorNumber), 
                                                        parentComponent=int(0), 
                                                        waitForConfirmation=True)
circle3.set_material_properties([1,0,0], roughness=0.7, metallic=False)

myCamera0 = QLabsFreeCamera (qlabs)
myCamera0.spawn_id(0, location=[24.142, -17.5, 14.233], rotation=[0, 0.576, 2.336])
myCamera1 = QLabsFreeCamera (qlabs)
myCamera1.spawn_id(1, location=[-7.782, 14.285, 50.271], rotation=[0, 1.393, -0.009])
myCamera2 = QLabsFreeCamera (qlabs)
myCamera2.spawn_id(2, location=[22.072, -14.007, 1.738], rotation=[0, -0.024, 2.433])
myCamera3 = QLabsFreeCamera (qlabs)
myCamera3.spawn_id(3, location=[30, -12.5, 35], rotation=[-0, 0.85, 2.419])
myCamera4 = QLabsFreeCamera (qlabs)
myCamera4.spawn_id(4, location=[-22.025, 23.081, 7.567], rotation=[0, 0.333, -0.896])

myCamera3.possess()

# traffic light
TrafficLight0 = QLabsTrafficLight(qlabs)
TrafficLight0.spawn_id_degrees(0, [-2.5, -5.5, 0], [0, 0, 90], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
TrafficLight0.set_color(QLabsTrafficLight.COLOR_GREEN)

TrafficLight1 = QLabsTrafficLight(qlabs)
TrafficLight1.spawn_id_degrees(1, [8, -12.7, 0], [0, 0, 270], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
TrafficLight1.set_color(QLabsTrafficLight.COLOR_RED)

TrafficLight2 = QLabsTrafficLight(qlabs)
TrafficLight2.spawn_id_degrees(2, [7.0, 13.5, 0.2], [0, 0, 90], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
TrafficLight2.set_color(QLabsTrafficLight.COLOR_RED)

# stop signs
myStopSign = QLabsStopSign(qlabs)
myStopSign.spawn_id_degrees(actorNumber=0, location=[9.0, 13.5, 0.2], rotation=[0, 0, 0], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myStopSign.spawn_id_degrees(actorNumber=1, location=[24.5, 4.5, 0.2], rotation=[0, 0, -90], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myStopSign.spawn_id_degrees(actorNumber=2, location=[4.7, 3, 0.2], rotation=[0, 0, -90], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myStopSign.spawn_id_degrees(actorNumber=3, location=[3, -13, 0.2], rotation=[0, 0, 180], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myStopSign.spawn_id_degrees(actorNumber=4, location=[9, -6.0, 0.2], rotation=[0, 0, 0], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myStopSign.spawn_id_degrees(actorNumber=5, location=[-5.0, 6.5, 0.2], rotation=[0, 0, 180], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)

# สร้างตัวแปรป้ายวงเวียน
myRoundaboutSign = QLabsRoundaboutSign(qlabs)
myRoundaboutSign.spawn_id_degrees(actorNumber=0, location=[10.6, 28.5, 0.2], rotation=[0, 0, 180], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myRoundaboutSign.spawn_id_degrees(actorNumber=1, location=[24.5, 33.0, 0.2], rotation=[0, 0, -90], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
myRoundaboutSign.spawn_id_degrees(actorNumber=2, location=[3.0, 40.2, 0.2], rotation=[0, 0, 180], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)

mySpline = QLabsSplineLine(qlabs)
mySpline.spawn_degrees(location=[2, -4.1, 0.05], rotation=[0, 0, 0], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)

# spawn a person
print("Spawning a person...")
myPerson = QLabsPerson(qlabs)
myPerson.spawn_id_degrees(actorNumber=0, location=[5.0, 0.0, 1.0], rotation=[0, 0, 180], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
myPerson.move_to(location=[-3.0, 0.0, 1.0], speed=QLabsPerson.WALK, waitForConfirmation=True)
myPerson.spawn_id_degrees(actorNumber=1, location=[-13.5, -10.0, 1.0], rotation=[0, 0, 45], scale=[1, 1, 1], configuration=0, waitForConfirmation=True)
myPerson.spawn_id_degrees(actorNumber=2, location=[5.0, 20.0, 1.0], rotation=[0, 0, 180], scale=[1.0, 1.0, 1.0], configuration=0, waitForConfirmation=True)
qlabs.close()
print("Done!")
