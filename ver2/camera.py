from threading import Thread
from time import time, sleep

import cv2
import ins
import os
import numpy as np

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

@ins.only
class Record(Thread):
    def __init__(self, frame_queue, replay_path=None, save=1):
        Thread.__init__(self)
        self.daemon = 1
        self.save = save
        self.read_count = 0
        self.write_count = 0
        self.replay_path = replay_path
        self.init_capture()
        self.rec_stop = False
        print('=' * 20 + 'Video recording...' + '=' * 20)
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
        if self.replay_path and len(self.replay_path)>1:
            self.cap = cv2.VideoCapture(self.replay_path)
            print('Initialize video capture from file:', self.replay_path)
            return
        if self.replay_path:
            cameraNumber = int(self.replay_path)
        else:
            cameraNumber = 0
        self.cap = cv2.VideoCapture(cameraNumber)
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
        while(self.cap.isOpened()):
            ret, frame = self.cap.read()
            if not self.replay_path:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            if not len(self.replay_path) > 1:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            self.read_count += 1
            while self.output_queue.full():
                if self.replay_path:
                    sleep(0.1)
                else:
                    try:
                        self.output_queue.get(timeout=0.00001)
                    except:
                        pass
            self.output_queue.put(frame)
            if ret == True and not self.replay_path:
                if self.save:
                    self.out.write(frame)
                self.write_count += 1
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
        print('=' * 20 + 'Record stopped' + '=' * 20)
        self.rec_stop = True
