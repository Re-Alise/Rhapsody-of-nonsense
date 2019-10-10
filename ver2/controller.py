from data import MASK
from queue import Queue
from camera import Record
from plane import Plane
from time import time, sleep

import ins, cv2
import numpy as np

delta_c = 0.02


MASK_ALL = np.zeros([240, 320],dtype=np.uint8)
MASK_ALL[0:240, 40:280] = 255

MASK_FORWARD = np.zeros([240, 320],dtype=np.uint8)
MASK_FORWARD[0:90, 40:280] = 255

MASK_TOP = np.zeros([240, 320],dtype=np.uint8)
MASK_TOP[10:60, 20:300] = 255

MASK_BUTTON = np.zeros([240, 320],dtype=np.uint8)
MASK_BUTTON[121:240, 0:320] = 255

MASK_LINE_MIDDLE = np.zeros([240, 320],dtype=np.uint8)
MASK_LINE_MIDDLE[90:150, 40:280] = 255

MASK_OWO = np.zeros([240, 320],dtype=np.uint8)
MASK_OWO[:, 120:200] = 255

MASK_RIGHT = np.zeros([240, 320],dtype=np.uint8)
MASK_RIGHT[106:320, 0:240] = 255

kernel = np.ones((3,3),np.uint8)  

@ins.only
class Controller():
    def __init__(self, debug=0, replay_path=None, save=1):
        self.frame_queue = Queue(1)
        self.feedback_queue = Queue(1)
        try:
            self.record = Record(self.frame_queue, replay_path=replay_path, save=save, feedback_queue=self.feedback_queue)
        except:
            print('Controller init failed')
            raise IOError

        self.replay_path = replay_path
        self.frame_new = None
        self.debug = debug
        self.last_center = (160, 120)
        self.c = 3.5
        # if not debug:
        if not replay_path:
            try:
                self.plane = Plane()
            except:
                print('owo')
                raise IOError

    def mission_start(self):
        # all mission fun return "ret, pitch, roll, yaw"
        if self.replay_path:
            self.stable(10)
            self.stop()
        else:
            # self.stable(10)
            self.forward(90, 40)
            # self.stop()
        pass

    def get_frame(self):
        self.frame_new = self.frame_queue.get()
        # print('get frame')

    def forward(self, pitch, sec=10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            # ret, _, roll, yaw = self._stabilize()
            ret, pitch_fector, roll, yaw = self._along()
            _, yy, _, thr = self._find_center(self.frame_new, MASK_OWO)
            if yy > 120:
                pitch_overrided = (yy - 120) * 0.8
            else:
                pitch_overrided = pitch * pitch_fector
            if self.debug:
                print('ret: {}\t pitch: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch, pitch_fector, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
                if self.replay_path:
                    continue
            self.plane.update(ret, pitch_overrided, roll, yaw)

    def stable(self, sec=10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            ret, pitch, roll, yaw = self._stabilize()
            if self.debug:
                print('ret: {}\t pitch: {}\t roll: {}\t yaw: {}'.format(ret, pitch, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
                if self.replay_path:
                    continue
            self.plane.update(ret, pitch, roll, yaw)


    def _stabilize(self, color='k'):
        try:
            print('Frame shape:', self.frame_new.shape)
            print('Mask shape:', MASK_ALL.shape)
        except:
            pass
        
        xx, yy, _, thr = self._find_center(self.frame_new, MASK_ALL)
        # Warning: Input for pitch is reversed
        pitch = (120-yy)
        roll = (xx-160)
        if self.debug:
            # show img
            pass
        return 1, pitch, roll, 0

    def _along(self, color='k'):
        xx, _, _, _ = self._find_center(self.frame_new, MASK_FORWARD)
        yaw = xx-160
        xx, _, _, _ = self._find_center(self.frame_new, MASK_LINE_MIDDLE)
        roll = xx-160
        # pitch_fector = min(50, (50 - abs(yaw))) / max(50, abs(yaw))
        if abs(yaw) > 40:
            pitch_fector = 0.3
        else:
            pitch_fector = 1
        return 1, pitch_fector, roll, yaw

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

    def convert(frame)
    """ an amazing threshold function"""
        frame = cv2.GaussianBlur(frame, (25, 25), 0)
        r = frame[,;,;2]
        g = frame[,;,;1]
        b = frame[,;,;0]
        c = b-r+200
        _, c_thr = cv2.threshold(b, 180, 255, cv2.THRESH_BINARY_INV)
        return c_thr

    def detect(frame):
        """辨識紅綠燈"""
        frame = cv2.GaussianBlur(frame, (25, 25), 0)
        r = frame[,;,;2]
        g = frame[,;,;1]
        b = frame[,;,;0]
        a = r-g+220
        b = b-r+200
        _, a_thr = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
        _, b_thr = cv2.threshold(b, 100, 255, cv2.THRESH_BINARY_INV)
        num1 = cv2.countNonZero(a_thr)
        num2 = cv2.countNonZero(b_thr)
        if num1>10000:
            if num2>7000:
                print("GG")
            else:
                print("R")
        else:
            if num2>7000:
                print("BB")
            else:
                print("XXX")

    def _find_center(self, frame, mask, color='k'):
        frame = cv2.GaussianBlur(frame, (25, 25), 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # _, thr = cv2.threshold(gray,60,255,cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 13, self.c)
        # thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel)
        thr = cv2.morphologyEx(thr, cv2.MORPH_OPEN, kernel)
        thr = cv2.bitwise_and(thr, thr, mask=mask)
        
        contours, _ = cv2.findContours(thr,1,2)
        sumX=0
        sumY=0
        sumW=0
        if len(contours) < 5:
            self.c -= delta_c
            if self.c < 0:
                self.c = 0
        else:
            self.c += delta_c

        for cnt in contours:
            M=cv2.moments(cnt)
            if M['m00']<100:
                continue
            sumX += M['m10']
            sumY += M['m01']
            sumW += M['m00']
            # M['M00'] weight
            # M['m10'] xMoment
            # M['m01'] yMoment
        # 全畫面的黑色的中心座標
        if sumW == 0:
            print('Not found')
            # return -1, -1, 0
            # return 160, 120, 0, ret_thr
            # cX = 120
            # cY = 160
            cX = self.last_center[0]
            cY = self.last_center[1]
        else:
            cX = sumX/sumW  
            cY = sumY/sumW
            self.last_center = (cX, cY)

        if self.debug:
            ret_thr = thr
            edited = np.copy(thr)
            edited = cv2.cvtColor(edited, cv2.COLOR_GRAY2BGR)
            cv2.circle(edited, (int(cX), int(cY)), 5, (178, 0, 192), -1)
            text_base_position = 140
            cv2.putText(edited, 'cX: {}'.format(cX), (0, text_base_position), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            cv2.putText(edited, 'cY: {}'.format(cY), (0, text_base_position+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            cv2.putText(edited, 'sumW: {}'.format(sumW), (0, text_base_position+40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            cv2.putText(edited, 'yaw: {}, roll: {}, pitch: {}'.format(self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output), (0, text_base_position+60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            while self.feedback_queue.full():
                try:
                    self.feedback_queue.get(timeout=0.00001)
                except:
                    pass
            self.feedback_queue.put(edited)
            if self.replay_path:
                cv2.imshow('Replay', cv2.hconcat([frame, edited]))
                while not cv2.waitKey(0) & 0xFF == ord(' '):
                    sleep(0.1)
        else:
            ret_thr = None
        return cX, cY, sumW, ret_thr

    def stop(self):
        self.record.stop_rec()
    pass

if __name__ == '__main__':
    try:
        c = Controller(1)
    except:
        print('=oxo=')
        exit()
    # c.record.start()
    # c.mission_start()
