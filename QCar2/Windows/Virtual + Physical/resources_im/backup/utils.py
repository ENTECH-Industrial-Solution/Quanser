from quanser.common import Timeout
from pal.utilities.stream import BasicStream
import numpy as np

class AlignedRGBCompressed():
    def __init__(self,ip='localhost',nonBlocking=True,manualStart=False,port='18999'):
        # self.depth  = np.empty((360,640,1), dtype = np.float32)
        self.rgb  = np.zeros((480,640,3), dtype = np.uint8) 
        self.num_ints = 691200
        self.ints_buffer = np.zeros((691200),dtype=np.int32)
        if not manualStart:
            self.__initDepthAlign()
        self.uri='tcpip://'+ip+':'+port
        self._timeout = Timeout(seconds=0, nanoseconds=1000000)
        self._handle = BasicStream(uri=self.uri,
                                    agent='C',
                                    receiveBuffer=np.zeros((691200),
                                                           dtype=np.float32),
                                    sendBufferSize=480*640*3,
                                    recvBufferSize=480*640*4*4,
                                    nonBlocking=nonBlocking,
                                    reshapeOrder='F')
        self._sendPacket = np.zeros((480,640,3),dtype=np.uint8)
        self.status_check('', iterations=20)

    def status_check(self, message, iterations=10):
        # blocking method to establish connection to the server stream.
        self._timeout = Timeout(seconds=0, nanoseconds=1000) #1000000
        counter = 0
        while not self._handle.connected:
            self._handle.checkConnection(timeout=self._timeout)
            counter += 1
            if self._handle.connected:
                print(message)
                break
            elif counter >= iterations:
                print('Server error: status check failed.')
                break

    def read(self):
        new = False
        self._timeout = Timeout(seconds=0, nanoseconds=100)
        if self._handle.connected:
            length = self._handle.clientStream.receive_ints(self.ints_buffer,self.num_ints)
            new, bytesReceived = self._handle.receive(timeout=self._timeout, iterations=5)
            print('in read')
            print(length)
            print(bytesReceived)
            # print('read:',new, bytesReceived)
            # if new is True, full packet was received
            if new:
                # encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                self.depth = self._handle.receiveBuffer[:,:,:1]
                self.rgb = self._handle.receiveBuffer[:,:,[3,2,1]].astype(np.uint8)

        else:
            self.status_check('Reconnected to Server')
        return new
    
    def read_reply(self,annotated_frame):

        # data received flag
        new = False

        # 1 us timeout parameter
        self._timeout = Timeout(seconds=0, nanoseconds=10000000)

        # set remaining packet to send
        self._sendPacket = annotated_frame

        # if connected to driver, send/receive
        if self._handle.connected:
            self._handle.send(self._sendPacket)
            new, bytesReceived = self._handle.receive(timeout=self._timeout, iterations=5)
            # print(new, bytesReceived)
            # if new is True, full packet was received
            if new:
                # encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                self.depth = self._handle.receiveBuffer[:,:,:1]
                self.rgb = self._handle.receiveBuffer[:,:,[3,2,1]].astype(np.uint8)

        else:
            self.status_check('Reconnected.')

        # if new is False, data is stale, else all is good
        return new

    def terminate(self):
        self._handle.terminate()

class QCar2DepthAligned():
    def __init__(self,ip='localhost',nonBlocking=True,manualStart=False,port='18777'):
        self.depth  = np.empty((480,640,1), dtype = np.float32)
        self.rgb  = np.empty((480,640,3), dtype = np.uint8) 
        if not manualStart:
            self.__initDepthAlign()
        self.uri='tcpip://'+ip+':'+port
        self._timeout = Timeout(seconds=0, nanoseconds=1000000)
        self._handle = BasicStream(uri=self.uri,
                                    agent='C',
                                    receiveBuffer=np.zeros((480,640,4),
                                                           dtype=np.float32),
                                    sendBufferSize=480*640*3,
                                    recvBufferSize=480*640*4*4,
                                    nonBlocking=nonBlocking,
                                    reshapeOrder='F')
        self._sendPacket = np.zeros((480,640,3),dtype=np.uint8)
        self.disconnected=False
        self.status_check('', iterations=20)

    def status_check(self, message, iterations=10):
        # blocking method to establish connection to the server stream.
        self._timeout = Timeout(seconds=0, nanoseconds=1000) #1000000
        counter = 0
        while not self._handle.connected:
            self._handle.checkConnection(timeout=self._timeout)
            counter += 1
            if self._handle.connected:
                print(message)
                break
            elif counter >= iterations:
                print('Server error: status check failed.')
                break

    def read(self):
        new = False
        self._timeout = Timeout(seconds=0, nanoseconds=100)
        if self._handle.connected:
            new, bytesReceived = self._handle.receive(timeout=self._timeout, iterations=5)
            # print('read:',new, bytesReceived)
            # if new is True, full packet was received
            if new:
                # encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                self.depth = self._handle.receiveBuffer[:,:,:1]
                self.rgb = self._handle.receiveBuffer[:,:,[3,2,1]].astype(np.uint8)

        else:
            self.status_check('Reconnected to Server')
            self.disconnected=True

        return new
    
    def read_reply(self,annotated_frame):

        # data received flag
        new = False

        # 1 us timeout parameter
        self._timeout = Timeout(seconds=0, nanoseconds=10000000)

        # set remaining packet to send
        self._sendPacket = annotated_frame

        # if connected to driver, send/receive
        if self._handle.connected:
            self._handle.send(self._sendPacket)
            new, bytesReceived = self._handle.receive(timeout=self._timeout, iterations=5)
            # print(new, bytesReceived)
            # if new is True, full packet was received
            if new:
                # encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                self.depth = self._handle.receiveBuffer[:,:,:1]
                self.rgb = self._handle.receiveBuffer[:,:,[3,2,1]].astype(np.uint8)

        else:
            self.status_check('Reconnected.')
            self.disconnected=True

        # if new is False, data is stale, else all is good
        return new

    def terminate(self):
        self._handle.terminate()

class YOLOPublisher():
    def __init__(self,ip='localhost',nonBlocking=False,port="18666"):

        self.uri='tcpip://'+ip+':'+port
        self._timeout = Timeout(seconds=0, nanoseconds=100000)
        self._handle = BasicStream(uri=self.uri,
                                    agent='C',
                                    sendBufferSize=4*2*4,
                                    nonBlocking=nonBlocking,
                                    reshapeOrder='F')
        self._sendPacket = np.zeros((4,2),dtype=np.float32)
        self.status_check('', iterations=20)

    def status_check(self, message, iterations=10):
        # blocking method to establish connection to the server stream.
        self._timeout = Timeout(seconds=0, nanoseconds=100000) #1000000
        counter = 0
        while not self._handle.connected:
            self._handle.checkConnection(timeout=self._timeout)
            counter += 1
            if self._handle.connected:
                print(message)
                break
            elif counter >= iterations:
                print('YOLO client error: status check failed.')
                break

    def send(self,yolodata):

        # data received flag
        new = False
        # 1 us timeout parameter
        self._timeout = Timeout(seconds=0, nanoseconds=100000)
        # set remaining packet to send
        self._sendPacket = yolodata
        # if connected to driver, send/receive
        if self._handle.connected:
            new = True
            self._handle.send(self._sendPacket)

        else:
            self.status_check('Reconnected to yolo client.')

        # if new is False, data is stale, else all is good
        return new

    def terminate(self):
        self._handle.terminate()