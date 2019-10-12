from threading import Thread
from time import time, sleep
from tool import *

import cv2
import os
import numpy as np

IMAGE_SIZE = (240, 320)

@only
class Record(Thread):
    def __init__(self, frame_queue, feedback_queue=None, source_path=None, save=1, debug=0):
        Thread.__init__(self)
        self.daemon = 1
        self.debug = debug
        self.save = save
        self.read_count = 0
        self.write_count = 0
        self.source_path = source_path
        self.feedback_queue = feedback_queue
        self.bin = np.zeros([240, 320, 3],dtype=np.uint8)
        try:
            self.init_capture()
        except:
            print('Record init failed')
            raise IOError

        self.rec_stop = False
        self.output_queue = frame_queue
        print('=' * 20 + 'recorder init finish' + '=' * 20)

    def init_capture(self):
        if self.source_path is not None:
            if isinstance(self.source_path, str):
                self.cap = cv2.VideoCapture(self.source_path)
                p(self.debug, 'Initialize video capture from file:', self.source_path)
            elif isinstance(self.source_path, int):
                self.cap = cv2.VideoCapture(self.source_path)
                p(self.debug, 'Initialize video capture from carema:', self.source_path)
            else:
                p(self.debug, 'Wrong source type:', type(self.source_path))
                raise TypeError

        else:
            self.cap = cv2.VideoCapture(0)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[1])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[0])
        except:
            p(True, 'setting carema fail')

        if self.save:
            print(1)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            # time_str = '/home/pi/Desktop/Rhapsody-of-nonsense/records/' + str(int(time()))
            time_str = str(int(time()))
            os.mkdir(time_str)
            print(2)
            self.out = cv2.VideoWriter(time_str + '/original' + '.avi', fourcc,
                            30, (IMAGE_SIZE[1], IMAGE_SIZE[0]))
        
            print(3)
        if not self.cap.isOpened():
            p(True, 'Failed to open video capture, aborted')
            raise IOError

    def run(self):
        display('=' * 20 + 'Video recording...' + '=' * 20)
        while(self.cap.isOpened()):
            ret, frame = self.cap.read()

            # 處理回放
            text_base_position = 0
            i = 0
            while not self.feedback_queue.empty():
                obj = self.feedback_queue.get()
                obj_type = type(obj)
                if obj_type == np.ndarray:
                    self.bin = cv2.cvtColor(obj, cv2.COLOR_GRAY2BGR)
                elif obj_type == tuple:
                    if obj[0] == 0:
                        cv2.line(self.bin, (160, obj[1]), (obj[2], obj[1]), (0, 0, 255), 3)
                    elif obj[0] == 1:
                        cv2.line(self.bin, (obj[1], 120), (obj[1], obj[2]), (0, 0, 255), 3)

                elif obj_type == str:
                    cv2.putText(self.bin, obj, (0, text_base_position + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                    i += 1

            if ret:
                if isinstance(self.source_path, str):
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                    if self.save:
                        print(frame.shape)
                        self.out.write(frame)#, self.bin]))
                        # print(cv2.hconcat([frame, self.bin]).shape)
                    self.write_count += 1
                self.read_count += 1

                # queue output
                while self.output_queue.full():
                    if self.source_path:
                        sleep(0.1)
                    else:
                        try:
                            self.output_queue.get(timeout=0.00001)
                        except:
                            pass
                self.output_queue.put(frame)

            if self.rec_stop:
                self.cap.release()
                if self.save:
                    self.out.release()
                break

    def stop_rec(self):
        # print("=OxO=")
        sleep(3)
        display('=' * 20 + 'Record stopped' + '=' * 20)
        self.rec_stop = True
