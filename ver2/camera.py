from threading import Thread
from time import time, sleep

import cv2
import ins
import os

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

@ins.only
class Record(Thread):
    def __init__(self, frame_queue):
        Thread.__init__(self)
        self.daemon = 1
        self.read_count = 0
        self.write_count = 0
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
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        time_str = str(int(time()))
        os.mkdir('./' + time_str)
        self.out = cv2.VideoWriter(time_str + '/original' + '.avi', fourcc,
                            10.0, (IMAGE_SIZE[0], IMAGE_SIZE[1]))
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
            self.dealt(frame)
            self.read_count += 1
            while self.output_queue.full():
                try:
                    self.output_queue.get(timeout=0.00001)
                except:
                    pass
            self.output_queue.put(frame)
            if ret == True:
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
                self.out.release()
                # self.out0.release()
                # self.out1.release()
                # self.out2.release()
                # self.out3.release()
                break

    def dealt(self, frame):
        pass

    def stop_rec(self):
        # print("=OxO=")
        sleep(3)
        print('=' * 20 + 'Record stopped' + '=' * 20)
        self.rec_stop = True
