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
    from pit.YOLO.nets import YOLOv8
    import cv2
    from quanser.common import Timeout
    from quanser.communications import Stream, StreamError, PollFlag
    import numpy as np
    from quanser.common import Timeout
    from quanser.devices import Aaaf5050McK12LED

    import datetime
except Exception as e:
    logging.error('Error at %s', 'importing', exc_info=e)

nonBlocking=True
LED=Aaaf5050McK12LED()
LED.open("spi://localhost:1?memsize=420,word=8,baud=3333333,lsb=off,frame=1", 33)
LED.writeColors([[0, 255, 0]], 33) 
# initializing variables
send_to_matlab=np.ones((480,640,3),dtype=np.uint8)*100
send_to_matlab_buffer=np.zeros((4,2),dtype=np.float32)
try:

    class BasicStream:
        '''Class object consisting of basic stream server/client functionality'''
        def __init__(self, uri, agent='S', receiveBuffer=np.zeros(1, dtype=np.float64), sendBufferSize=2048, 
                    recvBufferSize=2048, nonBlocking=False, verbose=False, reshapeOrder = 'C'):
            '''
            This functions simplifies functionality of the quanser_stream module to provide a
            simple server or client. \n
            \n
            uri - IP server and port in one string, eg. 'tcpip://IP_ADDRESS:PORT' \n
            agent - 'S' or 'C' string representing server or client respectively \n
            receiveBuffer - numpy buffer that will be used to determine the shape and size of data received \n
            sendBufferSize - (optional) size of send buffer, default is 2048 \n
            recvBufferSize - (optional) size of recv buffer, default is 2048 \n
            nonBlocking - set to False for blocking, or True for non-blocking connections \n
            \n
            Stream Server as an example running at IP 192.168.2.4 which receives two doubles from the client: \n
            >>> myServer = BasicStream('tcpip://localhost:18925', 'S', receiveBuffer=np.zeros((2, 1), dtype=np.float64))
            \n
            Stream Client as an example running at IP 192.168.2.7 which receives a 480 x 640 color image from the server: \n
            >>> myClient = BasicStream('tcpip://192.168.2.4:18925', 'C', receiveBuffer=np.zeros((480, 640, 3), dtype=np.uint8))

            '''
            self.agent 			= agent
            self.sendBufferSize = sendBufferSize
            self.recvBufferSize = recvBufferSize
            self.uri 			= uri
            self.receiveBuffer  = receiveBuffer
            self.verbose        = verbose
            self.reshapeOrder   = reshapeOrder  
            # reshape order need to be specified as "F" when reading images streamed from a MATLAB server

            # If the agent is a Client, then Server isn't needed.
            # If the agent is a Server, a Client will also be needed. The server can start listening immediately.

            self.clientStream = Stream()
            if agent=='S':
                self.serverStream = Stream()

            # Set polling timeout to 10 milliseconds
            self.t_out = Timeout(seconds=0, nanoseconds=10000000)

            # connected flag initialized to False
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
            '''When using non-blocking connections (nonBlocking set to True), the constructor method for this class does not block when
            listening (as a server) or connecting (as a client). In such cases, use the checkConnection method to attempt continuing to
            accept incoming connections (as a server) or connect to a server (as a client).  \n
            \n
            Stream Server as an example \n
            >>> while True:
            >>> 	if not myServer.connected:
            >>> 		myServer.checkConnection()
            >>>		if myServer.connected:
            >>> 		yourCodeGoesHere()
            \n
            Stream Client as an example \n
            >>> while True:
            >>> 	if not myClient.connected:
            >>> 		myClient.checkConnection()
            >>>		if myClient.connected:
            >>> 		yourCodeGoesHere()
            \n
            '''
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
            '''Use this method to correctly shutdown and then close connections. This method automatically closes all streams involved (Server will shutdown server streams as well as client streams). \n
            \n
            Stream Server as an example \n
            >>> while True:
            >>> 	if not myServer.connected:
            >>> 		myServer.checkConnection()
            >>>		if myServer.connected:
            >>> 		yourCodeGoesHere()
            >>>			if breakCondition:
            >>>				break
            >>> myServer.terminate()
            \n
            Stream Client as an example	 \n
            >>> while True:
            >>> 	if not myClient.connected:
            >>> 		myClient.checkConnection()
            >>>		if myClient.connected:
            >>> 		yourCodeGoesHere()
            >>>			if breakCondition:
            >>>				break
            >>> myClient.terminate()

            '''

            if self.connected:
                self.clientStream.shutdown()
                self.clientStream.close()
                if self.verbose: print('Successfully terminated clients...')

            if self.agent == 'S':
                self.serverStream.shutdown()
                self.serverStream.close()
                if self.verbose: print('Successfully terminated servers...')

        def receive(self, iterations=1, timeout=Timeout(seconds=0, nanoseconds=10)):
            '''
            This functions populates the receiveBuffer with bytes if available. \n \n

            Accepts: \n
            iterations - (optional) number of times to poll for incoming data before terminating, default is 1 \n
            \n
            Returns: \n
            receiveFlag - flag indicating whether the number of bytes received matches the expectation. To check the actual number of bytes received, use the bytesReceived class object. \n
            \n
            Stream Server as an example \n
            >>> while True:
            >>> 	if not myServer.connected:
            >>> 		myServer.checkConnection()
            >>>		if myServer.connected:
            >>> 		flag = myServer.receive()
            >>>			if breakCondition or not flag:
            >>>				break
            >>> myServer.terminate()
            \n
            Stream Client as an example	 \n
            >>> while True:
            >>> 	if not myClient.connected:
            >>> 		myClient.checkConnection()
            >>>		if myClient.connected:
            >>> 		flag = myServer.receive()
            >>>			if breakCondition or not flag:
            >>>				break
            >>> myClient.terminate()

            '''

            self.t_out = timeout
            counter = 0
            dataShape = self.receiveBuffer.shape

            # Find number of bytes per array cell based on type
            numBytesBasedOnType = len(np.array([0], dtype=self.receiveBuffer.dtype).tobytes())

            # Calculate total dimensions
            dim = 1
            for i in range(len(dataShape)):
                dim = dim*dataShape[i]

            # Calculate total number of bytes needed and set up the bytearray to receive that
            totalNumBytes = dim*numBytesBasedOnType
            self.data = bytearray(totalNumBytes)
            self.bytesReceived = 0
            # print(totalNumBytes)
            # Poll to see if data is incoming, and if so, receive it. Poll a max of 'iteration' times
            try:
                while True:

                    # See if data is available
                    pollResult = self.clientStream.poll(self.t_out, PollFlag.RECEIVE)
                    counter += 1
                    if not (iterations == 'Inf'):
                        if counter > iterations:
                            break
                    if not ((pollResult & PollFlag.RECEIVE) == PollFlag.RECEIVE):
                        continue # Data not available, skip receiving

                    # Receive data
                    self.bytesReceived = self.clientStream.receive_byte_array(self.data, totalNumBytes)

                    # data received, so break this loop
                    break

                #  convert byte array back into numpy array and reshape.
                self.receiveBuffer = np.reshape(np.frombuffer(self.data, dtype=self.receiveBuffer.dtype), dataShape, order = self.reshapeOrder)

            except StreamError as e:
                print(e.get_error_message())
            finally:
                receiveFlag = self.bytesReceived==1
                return receiveFlag, totalNumBytes*self.bytesReceived

        def send(self, buffer):
            """
            This functions sends the data in the numpy array buffer
            (server or client). \n \n

            INPUTS: \n
            buffer - numpy array of data to be sent \n

            OUTPUTS: \n
            bytesSent - number of bytes actually sent (-1 if send failed) \n
            \n
            Stream Server as an example \n
            >>> while True:
            >>> 	if not myServer.connected:
            >>> 		myServer.checkConnection()
            >>>		if myServer.connected:
            >>> 		sent = myServer.send()
            >>>			if breakCondition or sent == -1:
            >>>				break
            >>> myServer.terminate()
            \n
            Stream Client as an example	 \n
            >>> while True:
            >>> 	if not myClient.connected:
            >>> 		myClient.checkConnection()
            >>>		if myClient.connected:
            >>> 		sent = myServer.send()
            >>>			if breakCondition or sent == -1:
            >>>				break
            >>> myClient.terminate()

            """

            # Set up array to hold bytes to be sent
            byteArray = buffer.tobytes()
            self.bytesSent = 0

            # Send bytes and flush immediately after
            try:
                self.bytesSent = self.clientStream.send_byte_array(byteArray, len(byteArray))
                self.clientStream.flush()
            except StreamError as e:
                print(e.get_error_message())
                self.bytesSent = -1 # If an error occurs, set bytesSent to -1 for user to check
                self.dicconnected = True
            finally:
                return self.bytesSent
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
except Exception as e:
    logging.error('Error at %s', 'utility classes', exc_info=e)

myYolo=YOLOv8(imageWidth = 640,imageHeight = 480)
QCarImg=QCar2DepthAligned(nonBlocking=nonBlocking,manualStart=True)
yolo_out = YOLOPublisher(nonBlocking=nonBlocking)
try:
    while True:
        # if QCarImg.disconnected:
        #     break
        if QCarImg._handle.dicconnected:
            QCarImg=QCar2DepthAligned(nonBlocking=nonBlocking,manualStart=True)
            yolo_out = YOLOPublisher(nonBlocking=nonBlocking)
        
        QCarImg._handle.checkConnection()
        connected = QCarImg._handle.connected
        if not connected:
            pass
        if connected:
            new = QCarImg.read_reply(send_to_matlab)
            # new = QCarImg.read()
            if new:
                yolo_out.send(send_to_matlab_buffer)
                color_img=myYolo.pre_process(QCarImg.rgb)
                myYolo.predict(color_img,classes = [2,9,11,33])
                
                processed_results=myYolo.post_processing(QCarImg.depth)
                
                if processed_results is not None:
                    # show_processed(processed_results)
                    annotated_frame=myYolo.post_process_render()
                    # annotated_frame=myYolo.render()
                    send_to_matlab=myYolo.reshape_for_matlab_server(annotated_frame)
                    if len(processed_results)>0:
                        temp_buffer=[[] for _ in range (4)]
                        yoloBuffer=np.zeros((4,2),dtype=np.float32)
                        for i in processed_results:
                            # print(i.name)
                            if 'car' in i.name:
                                temp_buffer[0].append([i.conf,i.distance])
                            elif 'stop sign' in i.name:
                                temp_buffer[1].append([i.conf,i.distance])
                            elif 'red' in i.name:
                                temp_buffer[2].append([i.conf,i.distance])
                            elif 'yield' in i.name:
                                temp_buffer[3].append([i.conf,i.distance])
                            elif 'person' in i.name:
                                temp_buffer[4].append([i.conf,i.distance])
                        for j,result in enumerate(temp_buffer):
                            if len(result)>0:
                                result.sort(key=lambda x:x[1])
                                yoloBuffer[j]=result[0]
                        flatten = yoloBuffer.flatten(order='F')
                        send_to_matlab_buffer =flatten.reshape(yoloBuffer.shape,order='C')
                        # print(send_to_matlab_buffer)
                else:
                    send_to_matlab=myYolo.reshape_for_matlab_server(QCarImg.rgb)
                    send_to_matlab_buffer=np.zeros((4,2),dtype=np.float32)
except Exception as e:
    logging.error('Error at %s', 'running client', exc_info=e)
finally:
    QCarImg.terminate()
    yolo_out.terminate()
