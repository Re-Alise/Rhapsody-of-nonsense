from data import MASK
from queue import Queue
from camera import Record
from plane import Plane
from time import time, sleep

import ins, cv2
import numpy as np

para = 5


MASK_ALL = np.zeros([240, 320],dtype=np.uint8)
MASK_ALL[0:240, 40:280] = 255

MASK_FORWARD = np.zeros([240, 320],dtype=np.uint8)
MASK_FORWARD[10:90, 10:310] = 255

MASK_TOP = np.zeros([240, 320],dtype=np.uint8)
MASK_TOP[0:120, 0:320] = 255

MASK_BUTTON = np.zeros([240, 320],dtype=np.uint8)
MASK_BUTTON[121:240, 0:320] = 255

MASK_LINE_MIDDLE = np.zeros([240, 320],dtype=np.uint8)
MASK_LINE_MIDDLE[101:140, 81:240] = 255

MASK_RIGHT = np.zeros([240, 320],dtype=np.uint8)
MASK_RIGHT[106:320, 0:240] = 255

kernel = np.ones((7,7),np.uint8)  

@ins.only
class Controller():
    def __init__(self, debug=0, replay_path=None):
        self.frame_queue = Queue(1)
        self.record = Record(self.frame_queue, replay_path=replay_path)
        self.replay_path = replay_path
        self.frame_new = None
        self.debug = debug
        if not debug:
            self.plane = Plane()

    def mission_start(self):
        # all mission fun return "ret, pitch, roll, yaw"
        self.stable(30)
        self.stop()
        pass

    def get_frame(self):
        self.frame_new = self.frame_queue.get()
        # print('get frame')

    def stable(self, sec=10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            ret, pitch, roll, yaw = self._stabilize()
            if self.debug:
                print('ret: {}\t pitch: {}\t roll: {}\t yaw: {}'.format(ret, pitch, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
                continue
            self.plane.update(ret, pitch, roll, yaw)


    def _stabilize(self, color='k'):
        xx, yy, _, thr = self._find_center(self.frame_new, np.transpose(MASK_ALL))
        pitch = (160-yy)//para
        roll = (xx-120)//para
        if self.debug:
            # show img
            pass
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
        frame = cv2.GaussianBlur(frame, (25, 25), 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # _, thr = cv2.threshold(gray,78,255,cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 9, 2)
        # thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel)
        thr = cv2.morphologyEx(thr, cv2.MORPH_GRADIENT, kernel)
        thr = cv2.bitwise_and(thr, thr, mask=mask)
        
        contours, _ = cv2.findContours(thr,1,2)
        sumX=0
        sumY=0
        sumW=0
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
            cX = 120
            cY = 160
        else:
            cX = sumX/sumW  
            cY = sumY/sumW

        if self.debug:
            ret_thr = thr
            if self.replay_path:
                edited = np.copy(thr)
                edited = cv2.cvtColor(edited, cv2.COLOR_GRAY2BGR)
                cv2.circle(edited, (int(cX), int(cY)), 5, (178, 0, 192), -1)
                cv2.putText(edited, 'cX: {}'.format(cX), (0, edited.shape[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(edited, 'cY: {}'.format(cY), (0, edited.shape[1]+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(edited, 'sumW: {}'.format(sumW), (0, edited.shape[1]+40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
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
    c = Controller(1)
    c.record.start()
    c.mission_start()
