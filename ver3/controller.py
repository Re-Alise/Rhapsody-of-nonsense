from data import MASK
from queue import Queue
from camera import Record
from plane import Plane
from time import time, sleep
from tool import *

import numpy as np
import cv2

delta_c = 0.03
C_START = 3.5

kernel = np.ones((3,3),np.uint8)
kernel2 = np.ones((7,7),np.uint8)
IMAGE_SIZE = (320, 240) # 高寬

# MASK: width, hight, offset_x, offset_y
#       (half) (half) (right+)  (top+)
MASK_ALL = (None, None, 0, 0)
MASK_YAW_UP = (120, 40, 0, 80)
MASK_YAW_DOWN = (120, 40, 0, -80)
MASK_FORWARD = (230, 45, 0, 75)

@only
class Controller():
    def __init__(self, source_path=None, save=1, debug=0):
        """debug: manual read video (" ", "x"), and no use PIGPIO"""
        self.debug = debug
        self.frame_queue = Queue(1)
        self.feedback_queue = Queue()
        self.record = Record(self.frame_queue, debug=self.debug, feedback_queue=self.feedback_queue, source_path=source_path, save=save)
        self.source_path = source_path
        self.frame_new = None
        self.last_center = (120, 160)
        self.c = C_START
        self._stop = 0
        if not debug:
            try:
                self.plane = Plane()
            except:
                display('Error: Failed to connect plane')
                raise IOError
        elif __name__ == '__main__':
            self.plane = Plane(debug=1)

    def mission_start(self):
        # all mission fun return "ret, pitch, roll, yaw"
        if self.debug:
            self.stable()
            self.stop()
        else:
            self.stable(20)
            self.stop()
        pass


    def stable(self, sec=10):
        now = time()
        while time()-now<sec:
            if self._stop:
                self.stop()
                break
            self._get_frame()
            # check break condition
            ret, pitch, roll, yaw = self._stabilize()
            if self.debug:
                print('ret: {}\t pitch: {}\t roll: {}\t yaw: {}'.format(ret, pitch, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
            self.plane.update(ret, pitch, roll, yaw)
            self.frame_finish()

    def _stabilize(self, color='k'):
        # try:
        #     print('Frame shape:', self.frame_new.shape)
        #     print('Mask shape:', MASK_ALL.shape)
        # except:
        #     pass
        
        xx, yy, _, thr = self._find_center(mask=MASK_ALL)
        # Warning: Input for pitch is reversed
        pitch = (120-yy)
        roll = (xx-160)
        if self.debug:
            # show img
            pass
        return 1, pitch, roll, 0

    def _get_frame(self):
        frame = self.frame_queue.get()
        self.frame_new = frame
        self.binarized_frame = self._binarization_general(frame)
        # self.binarized_frame = self._binarization_low_light(frame)
        self.feedback_queue.put(self.binarized_frame)

    def _binarization_general(self, frame):
        frame = cv2.GaussianBlur(frame, (13, 13), 0)
        r = frame[:,:,2]
        b = frame[:, :, 0]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, gray_ = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
        c = b - r + 180
        c = np.asarray(c, np.uint8)
        _, c_ = cv2.threshold(c, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binarized_frame = np.bitwise_and(c_, gray_)
        self.feedback_queue.put(binarized_frame)
        return binarized_frame

    def _binarization_low_light(self, frame):
        frame = cv2.GaussianBlur(frame, (25, 25), 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, self.c)
        thr = cv2.morphologyEx(thr, cv2.MORPH_OPEN, kernel)
        thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel2)
        try:
            thr = cv2.bitwise_and(thr, thr)
        except:
            p(self.debug, 'Something went wrong when do bitwise operation')
            p(self.debug, 'Image shape: {}'.format(thr.shape))
        
        contours, _ = cv2.findContours(thr,1,2)
        sumX=0
        sumY=0
        sumW=0
        if len(contours) < 10:
            self.c -= delta_c
            if self.c < 0:
                self.c = 0
        else:
            self.c += delta_c

        self.feedback_queue.put(thr)
        return thr

    def _mask(self, mask=(None, None, 0, 0), img_size=IMAGE_SIZE):
        """mask -> (width, hight, offset_x, offset_y),width and hight are half value
        """
        width, hight, offset_x, offset_y = mask
        mask = np.zeros(img_size,dtype=np.uint8)
        center_point_x = img_size[1]//2 + offset_x
        center_point_y = img_size[0]//2 + offset_y
        if not hight and not width:
            return self.binarized_frame
        elif not hight:
            x1 = center_point_x-width
            x2 = center_point_x+width
            y1 = 0
            y2 = img_size[0]
            # vartical
            pass
        elif not width:
            x1 = 0
            x2 = img_size[1]
            y1 = center_point_y-hight
            y2 = center_point_y+hight
            # horz.tal
            pass
        else:
            x1 = center_point_x-width
            x2 = center_point_x+width
            y1 = center_point_y-hight
            y2 = center_point_y+hight
        
        mask[y1:y2,x1:x2] = 255
        masked = np.bitwise_and(self.binarized_frame, mask)
        return masked

    def _find_center(self, mask, error_num=10):
        thr =self._mask(mask=mask)

        contours, _ = cv2.findContours(thr,1,2)
        sumX=0
        sumY=0
        sumW=0
        if len(contours) < error_num:
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
            display('Not found')
            cX = self.last_center[0]
            cY = self.last_center[1]
        else:
            cX = sumX/sumW  
            cY = sumY/sumW
            self.last_center = (cX, cY)

        if self.debug:
            ret_thr = thr
            if self.source_path:
                cv2.imshow('Replay', self.frame_new)
                # cv2.imshow('Replay', cv2.hconcat([frame, edited]))
                while 1:
                    inn = cv2.waitKey(0)
                    if inn & 0xFF == ord(' '):
                        break
                    if inn & 0xFF == ord('x'):
                        self._stop = 1
                        break
                    sleep(0.1)
        else:
            ret_thr = None
        return cX, cY, sumW, ret_thr

    def frame_finish(self):
        self.feedback_queue.put('yaw: {}, roll: {}, pitch: {}'.format(self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output))

    def stop(self):
        self.record.stop_rec()

if __name__ == '__main__':
    try:
        # c = Controller(source_path=0, debug=1, save=0)
        # c = Controller(source_path='video/test1.avi', debug=1, save=0)
        c = Controller(source_path='1570714029/original.avi', debug=1, save=1)
        print('~~~')
    except Exception as e:
        print(e)
        print('Controller init fail')
        exit()
    c.record.start()
    c.mission_start()
