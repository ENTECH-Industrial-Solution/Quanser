import numpy as np
import time
from pit.YOLO.nets import YOLOv8
import cv2
from utils import QCar2DepthAligned,YOLOPublisher
from quanser.communications import Stream, StreamError, PollFlag
from quanser.common import Timeout
from quanser.devices import Aaaf5050McK12LED

def main():
    nonBlocking=True
    myYolo=YOLOv8(imageWidth = 640,imageHeight = 480)
    LED=Aaaf5050McK12LED()
    LED.open("spi://localhost:1?memsize=420,word=8,baud=3333333,lsb=off,frame=1", 33)
    LED.writeColors([[0, 255, 0]], 33) 
    # initializing variables
    send_to_matlab=np.ones((480,640,3),dtype=np.uint8)*100
    send_to_matlab_buffer=np.zeros((4,2),dtype=np.float32)

    QCarImg=QCar2DepthAligned(nonBlocking=nonBlocking,manualStart=True)
    yolo_out = YOLOPublisher(nonBlocking=nonBlocking)
    while True:
        if QCarImg.disconnected:
            break
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
    main()

if __name__ == '__main__':
    main()