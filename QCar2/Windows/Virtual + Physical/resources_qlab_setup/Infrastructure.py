from quanser.common import Timeout, ErrorCode
from quanser.communications import Stream, StreamError, PollFlag

from qvl.qlabs import QuanserInteractiveLabs
from qvl.environment_outdoors import QLabsEnvironmentOutdoors
from qvl.traffic_light import QLabsTrafficLight
from qvl.free_camera import QLabsFreeCamera


import keyboard
import struct
import time
import random
import sys



class QCarInfrastructure:

    MAX_CARS = 5
    data_to_cars = []
    
    uri = "tcpip://localhost:1111"
    send_buffer_size = 1460
    receive_buffer_size = 1460  
    
    read_buffer_size = 64
    read_buffer = bytearray(read_buffer_size)
    
    server_stream = None
    client_list = []
    
   
    def __init__(self):
        

        # Initialize xy array for number of cars
        for count in range(self.MAX_CARS):
            self.data_to_cars.append(10)
            self.data_to_cars.append(10)

        # Append traffic light state
        self.data_to_cars.append(0)
        
        print("\nStarting infrastructure server.")

        # Create a non-blocking stream server so we can
        # dynamically handle multiple connections
        self.server_stream = Stream()
        self.server_stream.listen(self.uri, True)

        print("Listening for connections...")
        
        
    def __del__(self):
        # Clean up any remaining connections and close the server stream

        for client in self.client_list:
            client.shutdown()
            print("Connection closed.")
            
        if (self.server_stream != None):
            self.server_stream.close()
        
        print("Server shutdown. Goodbye.")

    def Listen(self):
        # Check for a new connection
        timeout = Timeout(0)
        
        try:
            
            result = self.server_stream.poll(timeout, PollFlag.ACCEPT)
            
            if (result):
                print("Connection attempt...")
                client_connection = self.server_stream.accept(self.send_buffer_size, self.receive_buffer_size)
                
                if client_connection != None:
                    self.client_list.append(client_connection)
                    print("New connection accepted.")
                else:
                    print("Rejected connection attempt.")
            
        except StreamError as e:
            pass
            
    def ReceiveNewData(self):
        new_data = False
    
        # Check for new data from clients
        for client in self.client_list:
            try:
                bytes_read = client.receive(self.read_buffer, self.read_buffer_size)
                
                if (bytes_read >= 0):
                    #print("Received {} bytes".format(bytes_read))
                    
                    if (bytes_read >= 32):
                    
                        car_id, x, y, heading, = struct.unpack("<dddd", self.read_buffer[0:32])
                        index = round(car_id) - 1
                        #print("ID: {} x: {} y: {}, heading {}".format(index, x, y, heading))
                        
                        if (index >= 0) and (index < self.MAX_CARS):
                            self.data_to_cars[index] = x
                            self.data_to_cars[index + self.MAX_CARS] = y
                            
                        new_data = True

                    
                elif (bytes_read != -ErrorCode.WOULD_BLOCK):
                    print("Receive error code: {}".format(bytes_read))
                
                
            except StreamError as e:
                print("Client receive error: {}".format(e))
                
                pass
                
        return new_data

    def TransmitNewData(self, use_headlights, traffic_state):
        # Send out collective data to all clients
        shutdown_list = []
        
        for client_index in range(len(self.client_list)):
            client = self.client_list[client_index]
            send_array = bytearray()
            
            for index in range(self.MAX_CARS):
                send_array = send_array + bytearray(struct.pack("<dd",self.data_to_cars[index*2 + 0], self.data_to_cars[index*2 + 1]))
                
            
            send_array = send_array + bytearray(struct.pack("<d", traffic_state))
            send_array = send_array + bytearray(struct.pack("<d", use_headlights))
            
        
        
            try:
                bytes_sent = client.send(send_array, len(send_array))
                
            except StreamError as e:
                #print("Client send error: {}".format(e))
                # If we get an error, add this index to the list to be shutdown and removed.
                shutdown_list.append(client_index)   
                
                
                
        # Check if any connections need to be shutdown and removed
        if (len(shutdown_list) > 0):
            for client_index in reversed(shutdown_list):
                self.client_list[client_index].shutdown()
                self.client_list.pop(client_index)
                print("Closed client index {}, {} connections remaining".format(client_index, len(self.client_list)))
                
            # We don't know which connection was closed so reset all the transmit data.
            # In theory, this won't happen often so it shouldn't be much of a disruption,
            # but if that isn't the case, we'll need to track which connection is which car.
            
            for data in self.data_to_cars:
                data = 10


class QLabsEnvironment():
    qlabs = None
    hEnvironmentOutdoors = None
    
    environment_start_time = 0
    camera_start_time = 0
    use_headlights = False
    weather_selection = 0
    use_weather = True

    def __init__(self, UseWeather):
        self.qlabs = QuanserInteractiveLabs()
        print("Connecting to QLabs...")
        self.qlabs.open("localhost")
        
        self.use_weather = UseWeather
        
        if (UseWeather):
            self.hEnvironmentOutdoors = QLabsEnvironmentOutdoors(self.qlabs)
            
        self.environment_start_time = time.time()
        self.camera_start_time = time.time()
        
    def __del__(self):        
        if (self.qlabs != None):
            self.qlabs.close()
        
    def SetWeatherAndTimeOfDay(self):
    
        if (self.use_weather):
            weather_change = 30
            
            e = self.hEnvironmentOutdoors
            
            weather_options = [e.CLEAR_SKIES, e.CLEAR_SKIES, e.PARTLY_CLOUDY, e.RAIN, e.BLIZZARD]
        
            elapsed_time = time.time() - self.environment_start_time
            if elapsed_time >= weather_change:
                elapsed_time = elapsed_time - weather_change
                self.environment_start_time = self.environment_start_time + weather_change
                
                self.weather_selection = weather_options[random.randrange(0,len(weather_options))]
                
                self.hEnvironmentOutdoors.set_weather_preset(self.weather_selection)
                
                if (self.weather_selection >= 4):
                    self.use_headlights = True
                else:
                    self.use_headlights = False
                    
                self.hEnvironmentOutdoors.set_outdoor_lighting(self.use_headlights)
            
            #self.hEnvironmentOutdoors.set_time_of_day(elapsed_time/60*24) 
        
    def SelectCamera(self):
        camera_change = 11
        
        camera_options = [0, 1, 2, 3, 4]
    
        elapsed_time = time.time() - self.camera_start_time
        if elapsed_time >= camera_change:
            
            elapsed_time = elapsed_time - camera_change
            self.camera_start_time = self.camera_start_time + camera_change
            
            camera_selection = camera_options[random.randrange(0,len(camera_options))]
            
            hCamera = QLabsFreeCamera (self.qlabs)
            hCamera.actorNumber = camera_selection
            hCamera.possess()
            
    

def main(UseWeather):
    print("\n--------------------------------")
    print("Infrastructure - Hit ESC to exit")
    print("--------------------------------")
    Infrastructure = QCarInfrastructure()
    Environment = QLabsEnvironment(UseWeather)
    
    exit_loop = False
    
    
    while (exit_loop == False):
        
        # Communications
        Infrastructure.Listen()
        
        if (Infrastructure.ReceiveNewData()):
            Infrastructure.TransmitNewData(Environment.use_headlights, 0)
            
            
        else:
            # Only address environmental changes if you are not currently busy
            # with communications.  They need to be the highest priority.
            
            # Traffic Light 
            
            
            
            # Environment 
            
            Environment.SetWeatherAndTimeOfDay()
                
            Environment.SelectCamera()
        
        
        # User Interface 
        
        if (keyboard.is_pressed('ESC')):
            exit_loop = True


UseWeather = False

if(len(sys.argv) > 1):
    if (sys.argv[1] == "UseWeather"):
        UseWeather = True

main(UseWeather)