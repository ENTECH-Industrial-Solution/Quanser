import logging

logname='/home/nvidia/Desktop/yolo_client_log.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.info("Running YOLO client on start")

try:
    import numpy as np
    import time
    import threading
    import socket as _socket
    from pit.YOLO.nets import YOLOv8
    import cv2
    from quanser.common import Timeout
    from quanser.communications import Stream, StreamError, PollFlag
    from quanser.devices import Aaaf5050McK12LED
    import datetime
except Exception as e:
    logging.error('Error at %s', 'importing', exc_info=e)

nonBlocking = True


# ==============================================================================
# ค่าเริ่มต้น Buffer สำหรับส่งไปยัง Simulink และ QCar2
# ==============================================================================
send_to_matlab = np.ones((480, 640, 3), dtype=np.uint8) * 100
send_to_matlab_buffer = np.zeros((4, 2), dtype=np.float32)

try:

    class BasicStream:
        '''Class object consisting of basic stream server/client functionality'''
        def __init__(self, uri, agent='S', receiveBuffer=np.zeros(1, dtype=np.float64), sendBufferSize=2048,
                    recvBufferSize=2048, nonBlocking=False, verbose=False, reshapeOrder='C'):
            self.agent          = agent
            self.sendBufferSize = sendBufferSize
            self.recvBufferSize = recvBufferSize
            self.uri            = uri
            self.receiveBuffer  = receiveBuffer
            self.verbose        = verbose
            self.reshapeOrder   = reshapeOrder

            self.clientStream = Stream()
            if agent == 'S':
                self.serverStream = Stream()

            self.t_out = Timeout(seconds=0, nanoseconds=10000000)
            self.connected = False
            self.dicconnected = False

            try:
                if agent == 'C':
                    self.connected = self.clientStream.connect(uri, nonBlocking, self.sendBufferSize, self.recvBufferSize)
                    if self.connected and self.verbose:
                        print('Connected to a Server successfully.')
                elif agent == 'S':
                    if self.verbose:
                        print('Listening for incoming connections.')
                    self.serverStream.listen(self.uri, nonBlocking)
                pass
            except StreamError as e:
                if self.agent == 'S' and self.verbose:
                    print('Server initialization failed.')
                elif self.agent == 'C' and self.verbose:
                    print('Client initialization failed.')
                print(e.get_error_message())

        def checkConnection(self, timeout=Timeout(seconds=0, nanoseconds=100)):
            if self.agent == 'C' and not self.connected:
                try:
                    pollResult = self.clientStream.poll(timeout, PollFlag.CONNECT)
                    if (pollResult & PollFlag.CONNECT) == PollFlag.CONNECT:
                        self.connected = True
                        if self.verbose: print('Connected to a Server successfully.')
                except StreamError as e:
                    if e.error_code == -33:
                        self.connected = self.clientStream.connect(self.uri, True, self.sendBufferSize, self.recvBufferSize)
                    else:
                        if self.verbose: print('Client initialization failed.')
                        print(e.get_error_message())

            if self.agent == 'S' and not self.connected:
                try:
                    pollResult = self.serverStream.poll(self.t_out, PollFlag.ACCEPT)
                    if (pollResult & PollFlag.ACCEPT) == PollFlag.ACCEPT:
                        self.connected = True
                        if self.verbose: print('Found a Client successfully...')
                        self.clientStream = self.serverStream.accept(self.sendBufferSize, self.recvBufferSize)
                except StreamError as e:
                    if self.verbose: print('Server initialization failed...')
                    print(e.get_error_message())

        def terminate(self):
            if self.connected:
                self.clientStream.shutdown()
                self.clientStream.close()
                if self.verbose: print('Successfully terminated clients...')
            if self.agent == 'S':
                self.serverStream.shutdown()
                self.serverStream.close()
                if self.verbose: print('Successfully terminated servers...')

        def receive(self, iterations=1, timeout=Timeout(seconds=0, nanoseconds=10)):
            self.t_out = timeout
            counter = 0
            dataShape = self.receiveBuffer.shape

            numBytesBasedOnType = len(np.array([0], dtype=self.receiveBuffer.dtype).tobytes())

            dim = 1
            for i in range(len(dataShape)):
                dim = dim * dataShape[i]

            totalNumBytes = dim * numBytesBasedOnType
            self.data = bytearray(totalNumBytes)
            self.bytesReceived = 0
            try:
                while True:
                    pollResult = self.clientStream.poll(self.t_out, PollFlag.RECEIVE)
                    counter += 1
                    if not (iterations == 'Inf'):
                        if counter > iterations:
                            break
                    if not ((pollResult & PollFlag.RECEIVE) == PollFlag.RECEIVE):
                        continue

                    self.bytesReceived = self.clientStream.receive_byte_array(self.data, totalNumBytes)
                    break

                self.receiveBuffer = np.reshape(np.frombuffer(self.data, dtype=self.receiveBuffer.dtype), dataShape, order=self.reshapeOrder)

            except StreamError as e:
                print(e.get_error_message())
            finally:
                receiveFlag = self.bytesReceived == 1
                return receiveFlag, totalNumBytes * self.bytesReceived

        def send(self, buffer):
            byteArray = buffer.tobytes()
            self.bytesSent = 0
            try:
                self.bytesSent = self.clientStream.send_byte_array(byteArray, len(byteArray))
                self.clientStream.flush()
            except StreamError as e:
                print(e.get_error_message())
                self.bytesSent = -1
                self.dicconnected = True
            finally:
                return self.bytesSent

    class QCar2DepthAligned():
        def __init__(self, ip='localhost', nonBlocking=True, manualStart=False, port='18777'):
            self.depth = np.empty((480, 640, 1), dtype=np.float32)
            self.rgb = np.empty((480, 640, 3), dtype=np.uint8)
            if not manualStart:
                self.__initDepthAlign()
            self.uri = 'tcpip://' + ip + ':' + port
            self._timeout = Timeout(seconds=0, nanoseconds=1000000)
            self._handle = BasicStream(uri=self.uri,
                                       agent='C',
                                       receiveBuffer=np.zeros((480, 640, 4), dtype=np.float32),
                                       sendBufferSize=480 * 640 * 3,
                                       recvBufferSize=480 * 640 * 4 * 4,
                                       nonBlocking=nonBlocking,
                                       reshapeOrder='F')
            self._sendPacket = np.zeros((480, 640, 3), dtype=np.uint8)
            self.disconnected = False
            self.status_check('', iterations=20)

        def status_check(self, message, iterations=10):
            self._timeout = Timeout(seconds=0, nanoseconds=1000)
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
                if new:
                    self.depth = self._handle.receiveBuffer[:, :, :1]
                    self.rgb = self._handle.receiveBuffer[:, :, [3, 2, 1]].astype(np.uint8)
            else:
                self.status_check('Reconnected to Server')
                self.disconnected = True
            return new

        def read_reply(self, annotated_frame):
            new = False
            self._timeout = Timeout(seconds=0, nanoseconds=10000000)
            self._sendPacket = annotated_frame
            if self._handle.connected:
                self._handle.send(self._sendPacket)
                new, bytesReceived = self._handle.receive(timeout=self._timeout, iterations=5)
                if new:
                    self.depth = self._handle.receiveBuffer[:, :, :1]
                    self.rgb = self._handle.receiveBuffer[:, :, [3, 2, 1]].astype(np.uint8)
            else:
                self.status_check('Reconnected.')
                self.disconnected = True
            return new

        def terminate(self):
            self._handle.terminate()

    class YOLOPublisher():
        def __init__(self, ip='localhost', nonBlocking=False, port="18666"):
            self.uri = 'tcpip://' + ip + ':' + port
            self._timeout = Timeout(seconds=0, nanoseconds=100000)
            self._handle = BasicStream(uri=self.uri,
                                       agent='C',
                                       sendBufferSize=4 * 2 * 4,
                                       nonBlocking=nonBlocking,
                                       reshapeOrder='F')
            self._sendPacket = np.zeros((4, 2), dtype=np.float32)
            self.status_check('', iterations=20)

        def status_check(self, message, iterations=10):
            self._timeout = Timeout(seconds=0, nanoseconds=100000)
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

        def send(self, yolodata):
            new = False
            self._timeout = Timeout(seconds=0, nanoseconds=100000)
            self._sendPacket = yolodata
            if self._handle.connected:
                new = True
                self._handle.send(self._sendPacket)
            else:
                self.status_check('Reconnected to yolo client.')
            return new

        def terminate(self):
            self._handle.terminate()

except Exception as e:
    logging.error('Error at %s', 'utility classes', exc_info=e)

myYolo = YOLOv8(imageWidth=640, imageHeight=480)
QCarImg = QCar2DepthAligned(nonBlocking=nonBlocking, manualStart=True)
yolo_out = YOLOPublisher(nonBlocking=nonBlocking)

try:
    while True:
        # ตรวจสอบ disconnect ทั้ง 2 stream แยกกัน
        if QCarImg._handle.dicconnected:
            print("[Reconnect] QCarImg disconnected, recreating...")
            QCarImg = QCar2DepthAligned(nonBlocking=nonBlocking, manualStart=True)
            yolo_out = YOLOPublisher(nonBlocking=nonBlocking)
        elif yolo_out._handle.dicconnected:
            # yolo_out disconnect อย่างเดียว -> reconnect แค่ yolo_out
            print("[Reconnect] yolo_out disconnected, reconnecting YOLO publisher...")
            yolo_out = YOLOPublisher(nonBlocking=nonBlocking)

        QCarImg._handle.checkConnection()
        connected = QCarImg._handle.connected
        if not connected:
            pass
        if connected:
            new = QCarImg.read_reply(send_to_matlab)
            if new:
                yolo_out.send(send_to_matlab_buffer)
                color_img = myYolo.pre_process(QCarImg.rgb)
                myYolo.predict(color_img, classes=[2, 9, 11, 33])

                processed_results = myYolo.post_processing(QCarImg.depth)

                if processed_results is not None:
                    annotated_frame = myYolo.post_process_render()
                    send_to_matlab = myYolo.reshape_for_matlab_server(annotated_frame)
                    if len(processed_results) > 0:
                        temp_buffer = [[] for _ in range(4)]
                        yoloBuffer = np.zeros((4, 2), dtype=np.float32)
                        for i in processed_results:
                            if 'car' in i.name:
                                temp_buffer[0].append([i.conf, i.distance])
                            elif 'stop sign' in i.name:
                                temp_buffer[1].append([i.conf, i.distance])
                            elif 'red' in i.name:
                                temp_buffer[2].append([i.conf, i.distance])
                            elif 'yield' in i.name:
                                temp_buffer[3].append([i.conf, i.distance])
                        for j, result in enumerate(temp_buffer):
                            if len(result) > 0:
                                result.sort(key=lambda x: x[1])
                                yoloBuffer[j] = result[0]
                        flatten = yoloBuffer.flatten(order='F')
                        send_to_matlab_buffer = flatten.reshape(yoloBuffer.shape, order='C')
                else:
                    send_to_matlab = myYolo.reshape_for_matlab_server(QCarImg.rgb)
                    send_to_matlab_buffer = np.zeros((4, 2), dtype=np.float32)

except Exception as e:
    logging.error('Error at %s', 'running client', exc_info=e)
finally:
    QCarImg.terminate()
    yolo_out.terminate()
