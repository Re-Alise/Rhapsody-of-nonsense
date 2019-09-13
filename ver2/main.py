from time import time, sleep
from threading import Thread
from queue import Queue
from plane import Plane
from sonic import Sonic
from tfmini import TFMiniLidar
from data import PIN, DC, MASK
from camera import Record

import pigpio
import os
import ins
import cv2


BUZZER_INTERVAL_L = 0.5
BUZZER_INTERVAL_H = 1 - BUZZER_INTERVAL_L

buzzer_time = time()
buzzer_state = 0

para = 20

def beep(pi):
    global buzzer_time, buzzer_state
    # print(buzzer_time)
    delta = abs(time() - buzzer_time)
    if buzzer_state == 0:
        interval = BUZZER_INTERVAL_L
    else:
        interval = BUZZER_INTERVAL_H 
    if delta > interval:
        # global buzzer_time
        buzzer_state = abs(buzzer_state - 1)
        pi.write(PIN.BUZZER, buzzer_state)
        buzzer_time = time()

@ins.only
class Controller():
    def __init__(self):
        self.frame_queue = Queue(1)
        self.record = Record(self.frame_queue)
        self.plane = Plane()
        self.frame_new = None

    def mission_start(self):
        # all mission fun return "ret, pitch, roll, yaw"
        pass

    def get_frame(self):
        self.frame_new = self.frame_queue.get()

    def stable(self, sec = 10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            self.plane.update(self._stabilize())


    def _stabilize(self, color='k'):
        xx, yy, _ = self._find_center(self.frame_new, MASK.ALL)
        pitch = 120-yy
        roll = xx-160
        return 1, pitch, roll, 0

    # def _along(self, frame, color):
    #     xx, _, _ = self._find_center(frame, MASK_FORWARD)
    #     yaw = xx-160
    #     _, yy, _ = self._find_center(frame, MASK_LINE_MIDDLE)
    #     row = 120-yy
    #     pass

    # def _around(self, frame, color):
    #     _, yy, _ = self._find_center(frame, MASK_RIGHT)
    #     row = 120-yy
    #     _, _, w1 = self._find_center(frame, MASK_TOP)
    #     _, _, w2 = self._find_center(frame, MASK_BUTTON)
    #     yaw = w1-w2
    #     pass

    # def _detect(self, frame):
    #     _, _, ww = self._find_center(frame, MASK_ALL)
    #     if ww > self.something:
    #         return 1
    #     else:
    #         return 0

    def _find_center(self, frame, mask, color='k'):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thr = cv2.threshold(gray,100,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        thr = cv2.bitwise_and(thr, thr, mask=mask)
        contours, _ = cv2.findContours(thr,1,2)
        sumX=0
        sumY=0
        sumW=0
        for cnt in contours:
            M=cv2.moments(cnt)
            sumX += M['m10']
            sumY += M['m01']
            sumW += M['m00']
            # M['M00'] weight
            # M['m10'] xMoment
            # M['m01'] yMoment
        # 全畫面的黑色的中心座標
        if sumW == 0:
            print('Not found')
            return -1, -1, 0
        cX = sumX/sumW
        cY = sumY/sumW
        return cX//para, cY//para, sumW


    def stop(self):
        self.record.stop_rec()
    pass

if __name__ == '__main__':
    gpio = ins.get_only(pigpio.pi)
    gpio.set_mode(PIN.BUZZER, pigpio.OUTPUT)
    plane = Plane()
    controller = Controller()
    mode_auto = gpio.read(PIN.STATE)                          
                                                                         
    print('init finish-------------------------------')
    while 1:
        try:
            start_signal = gpio.read(PIN.STATE)
            if start_signal and not mode_auto:
                gpio.write(PIN.BUZZER, 0)
                mode_auto = 1
                # auto run
                print('mission start')
                controller.record.start()
                plane.arm()
                plane.mc(DC.OpticsFlow)
                plane.take_off(70, 22)
                plane.take_off(120, 10)
                plane.idle(5)
                controller.mission_start()

                plane.land()
                plane.mc(DC.Manual)
                plane.disarm()
                controller.stop()
                print('mission completed')
            else:
                if not start_signal:
                    mode_auto = 0
            # print(start_signal)
            beep(gpio)
            sleep(.1)
        except KeyboardInterrupt:
            print('owo')
            gpio.write(PIN.BUZZER, 0)
            break

