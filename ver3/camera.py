from threading import Thread
from time import time, sleep
from tool import *

import cv2
import os
import numpy as np

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

@only
class Record(Thread):
    def __init__(self, frame_queue, source_path=None, save=1, debug=0):
        Thread.__init__(self)
        self.daemon = 1
        self.debug = debug
        self.save = save
        self.read_count = 0
        self.write_count = 0
        self.source_path = source_path
        try:
            self.init_capture()
        except:
            raise IOError

        self.rec_stop = False
        self.output_queue = frame_queue
        

    def threshold(self, frame):
        r = frame[:,:,2]
        g = frame[:,:,1]
        b = frame[:, :, 0]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        ret3,th1 = cv2.threshold(r+100,150,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        ret3,th2 = cv2.threshold(g+100,120,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        ret3,th3 = cv2.threshold(b+100,100,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        ret3,th0 = cv2.threshold(gray,100,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        return th0, th1, th2, th3

    def init_capture(self):
        if self.source_path != None:
            if isinstance(self.source_path, str):
                self.cap = cv2.VideoCapture(self.source_path)
                p(self.debug, 'Initialize video capture from file:', self.source_path)
                return
            elif isinstance(self.source_path, int):
                self.cap = cv2.VideoCapture(self.source_path)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
                p(self.debug, 'Initialize video capture from file:', self.source_path)
            else:
                p(self.debug, 'Wrong source type:', type(self.source_path))
                raise TypeError

            if not self.cap.isOpened():
                p(True, 'Failed to open video capture, aborted')
                raise IOError

            return

        else:
            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                p(True, 'Failed to open video capture, aborted')
                raise IOError

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
            if self.save:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                time_str = '/home/pi/Desktop/Rhapsody-of-nonsense/records/' + str(int(time()))
                os.mkdir(time_str)
                self.out = cv2.VideoWriter(time_str + '/original' + '.avi', fourcc,
                                10.0, (IMAGE_SIZE[1], IMAGE_SIZE[0]))

        # self.out0 = cv2.VideoWriter(time_str + '/gray' + '.avi', fourcc,
        #                     10.0, (IMAGE_SIZE[0], IMAGE_SIZE[1]))
        # self.out1 = cv2.VideoWriter(time_str + '/r' + '.avi', fourcc,
        #                     10.0, (IMAGE_SIZE[0], IMAGE_SIZE[1]))
        # self.out2 = cv2.VideoWriter(time_str + '/g' + '.avi', fourcc,
        #                     10.0, (IMAGE_SIZE[0], IMAGE_SIZE[1]))
        # self.out3 = cv2.VideoWriter(time_str + '/b' + '.avi', fourcc,
        #                     10.0, (IMAGE_SIZE[0], IMAGE_SIZE[1]))

    def run(self):
        display('=' * 20 + 'Video recording...' + '=' * 20)
        while(self.cap.isOpened()):
            ret, frame = self.cap.read()
            if ret:
                if self.source_path == None or isinstance(self.source_path, int):
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                    if self.save:
                        self.out.write(frame)
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

                # th0, th1, th2, th3 = self.threshold(frame)
                # self.out0.write(cv2.cvtColor(th0, cv2.COLOR_GRAY2BGR))
                # self.out1.write(cv2.cvtColor(th1, cv2.COLOR_GRAY2BGR))
                # self.out2.write(cv2.cvtColor(th2, cv2.COLOR_GRAY2BGR))
                # self.out3.write(cv2.cvtColor(th3, cv2.COLOR_GRAY2BGR))
                # cv2.imshow('VideoWriter test', frame)

            if self.rec_stop:
                self.cap.release()
                if self.save:
                    self.out.release()
                # self.out0.release()
                # self.out1.release()
                # self.out2.release()
                # self.out3.release()
                break

    def stop_rec(self):
        # print("=OxO=")
        sleep(3)
        display('=' * 20 + 'Record stopped' + '=' * 20)
        self.rec_stop = True
