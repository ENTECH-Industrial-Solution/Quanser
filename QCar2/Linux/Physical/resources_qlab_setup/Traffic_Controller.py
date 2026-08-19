import time
import math
import struct
import keyboard
import argparse

from quanser.communications import Stream
import urllib.request, sys
from urllib.error import HTTPError, URLError
from socket import timeout


parser = argparse.ArgumentParser()
parser.add_argument('-ip','--traffic_ip', type=str, default='192.168.2.20', help='IP of the traffic light')
args = parser.parse_args()
ip = args.traffic_ip

#Send the formatted request
def sendreq(url):
    #Format the HTTP get request with a timeout of 1s to account for async tasks that will not return

    response = "Call complete!"
    try:
        response = urllib.request.urlopen(url, timeout=1).read().decode('utf-8')
    #If the URL is not correct
    except (HTTPError, URLError) as error:
        response = "Error endpoint not found at " + url
    #If the request was not expected to return the call it complete, otherwise flag a timeout
    except timeout:
        if url.find("timed") == -1:
            response = "Call timed out"
        else:
            response = "Async call complete"

    return response


from qvl.qlabs import QuanserInteractiveLabs
from qvl.traffic_light import QLabsTrafficLight

# creates a server connection with Quanser Interactive Labs and manages the communications
qlabs = QuanserInteractiveLabs()

print("Connecting to QLabs...")
# trying to connect to QLabs and open the instance we have created - program will end if this fails
try:
    qlabs.open("localhost")
except:
    print("Unable to connect to QLabs")

# traffic light (Connect to existing actors created by SetupEnvironment)
TrafficLight0 = QLabsTrafficLight(qlabs)
TrafficLight0.actorNumber = 0

TrafficLight1 = QLabsTrafficLight(qlabs)
TrafficLight1.actorNumber = 1

stream = Stream()
print("Connecting to Infrastructure Server on port 12000...")
connected = False
for _ in range(10):
    try:
        stream.connect("tcpip://localhost:12000", False, 64, 64)
        connected = True
        print("Connected to Infrastructure Server!")
        break
    except Exception as e:
        print("Waiting for Infrastructure Server to start...")
        time.sleep(1)

if not connected:
    print("Failed to connect to Infrastructure Server after 10 attempts.")
    sys.exit(1)
buffer = bytearray(16)

i = 0
continue_loop = True
last_x = None
while (continue_loop):
    i=i+1
    print (i)
    bytes_read = stream.receive(buffer, 16)
    try:
        x, y = struct.unpack("dd", buffer)
        print(f"Step {i}: Received x = {x}, y = {y}")
    except struct.error:
        # Fallback if it's only 8 bytes
        x, = struct.unpack("d", buffer[:8])
        print(f"Step {i}: Received x = {x} (8 bytes only)")

            # User Interface 
        
    if (keyboard.is_pressed('ESC')):
            continue_loop = False

    if x != last_x:
        if x == 1:
            TrafficLight0.set_color(QLabsTrafficLight.COLOR_GREEN)
            TrafficLight1.set_color(QLabsTrafficLight.COLOR_RED)
            print("Switched to GREEN/RED")
        else:
            TrafficLight0.set_color(QLabsTrafficLight.COLOR_RED)
            TrafficLight1.set_color(QLabsTrafficLight.COLOR_GREEN)
            print("Switched to RED/GREEN")
        
        last_x = x

stream.shutdown()
stream.close()

qlabs.close()
print("Done!")  
