from data import MASK
from queue import Queue
from camera import Record
from plane import Plane
from time import time, sleep
from tool import *
from box import Box

import numpy as np
import cv2

delta_c = 0.03
C_START = 3.5

kernel = np.ones((3,3),np.uint8)
kernel2 = np.ones((7,7),np.uint8)
IMAGE_SIZE = (240, 320) # 高寬

# MASK: width, hight, offset_x, offset_y
#       (half) (half) (right+)  (top+)
MASK_ALL = (None, None, 0, 0)
MASK_YAW_UP = (120, 40, 0, 80)
MASK_YAW_DOWN = (120, 40, 0, -80)
MASK_FORWARD = (115, 45, 0, 75)
MASK_LINE_MIDDLE = (None, 30, 0, 0)
MASK_OWO = (40, None, 0, 0)

@only
class Controller():
    def __init__(self, source_path=None, save_path=None, save=1, debug=0):
        """debug: manual read video (" ", "x"), and no use PIGPIO"""
        self.debug = debug
        self.frame_queue = Queue(1)
        self.feedback_queue = Queue()
        self.record = Record(self.frame_queue, debug=self.debug, feedback_queue=self.feedback_queue, source_path=source_path, save=save, save_path=save_path)
        self.source_path = source_path
        self.frame_new = None
        self.c = C_START
        self._stop = 0
        self.box = Box()
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
            self.forward(30, 20)
            self.stop()
        else:
            self.stable(20)
            self.stop()
        pass

    def loop(self, func_loop, func_condition, sec=10):
        now = time()
        while time()-now<sec | func_condition():
            if self._stop:
                break
            self._get_frame()
            func_loop()
            self.frame_finish()

    def forward(self, pitch, sec=10):
        now = time()
        while time()-now<sec:
            if self._stop:
                break
            self._get_frame()
            # check break condition
            # ret, _, roll, yaw = self._stabilize()
            ret, pitch_fector, roll, yaw = self._along()
            pitch_ = self._find_center(mask=MASK_OWO, data='y')

            pitch_overrided = int(pitch * pitch_fector)
            # if yy > 150:
            #     pitch_overrided += int(pitch_ * -1.0)
            # else:
            #     pitch_overrided = int(pitch * pitch_fector)

            if self.detect(self.frame_new) == 'R':
                self.box.drop()
                # pitch_overrided = 0
            else:
                self.box.close()
            
            if self.debug:
                print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch_overrided, pitch_fector, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
            # Testing
            # self.plane.update(ret, pitch_overrided, roll, yaw)
            self.plane.update(ret, pitch, roll, 0)
            self.frame_finish()


    def stable(self, sec=10):
        now = time()
        while time()-now<sec:
            if self._stop:
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
        pitch = self._find_center(mask=MASK_OWO, data='y')
        roll = self._find_center(mask=MASK_LINE_MIDDLE, data='x')
        return 1, pitch, roll, 0

    def _along(self, color='k'):
        yaw = self._find_center(mask=MASK_FORWARD, data='x')
        roll = self._find_center(mask=MASK_LINE_MIDDLE, data='x')
        # pitch_fector = min(50, (50 - abs(yaw))) / max(50, abs(yaw))
        if abs(yaw) > 40:
            # pitch_fector = 0.3
            pitch_fector = 1
        else:
            pitch_fector = 1
        return 1, pitch_fector, roll, yaw

    def detect(self, frame):
        """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。
        """
        sframe = cv2.GaussianBlur(frame, (13, 13), 0)
        r = sframe[:,:,2]
        g = sframe[:,:,1]
        b = sframe[:, :, 0]
        a = r-g+220
        c = b-r+220
        ans = cv2.hconcat([a, c])
        ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
        _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
        _, c = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY_INV)
        na = cv2.countNonZero(a)
        nb = cv2.countNonZero(c)
        if na>5000:
            if nb>2500:
                print("G", na, nb)
                return 'G'
            else:
                print("R", na, nb)
                return 'R'
        else:
            if nb>2500:
                print("B", na, nb)
                return 'B'
            else:
                print("XX", na, nb)
                return 'X'
        return ans

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
        center_point_y = img_size[0]//2 - offset_y

        if not width:
            x1 = 0
            x2 = img_size[1]
        else:
            x1 = center_point_x-width
            x2 = center_point_x+width

        if not hight:
            y1 = 0
            y2 = img_size[0]
        else:
            y1 = center_point_y-hight
            y2 = center_point_y+hight
        
        mask[y1:y2,x1:x2] = 255
        self.feedback_queue.put((1, (x1, y1), (x2, y2)))
        masked = np.bitwise_and(self.binarized_frame, mask)
        return masked

    def _find_center(self, mask, data, error_num=10):
        "mask: (width, hight, offset_x, offset_y),\ndata: 'x', 'y', 'w'"
        thr =self._mask(mask=mask)

        center_point_x = IMAGE_SIZE[1]//2 + mask[2]
        center_point_y = IMAGE_SIZE[0]//2 - mask[3]
        sumX=0
        sumY=0
        sumW=0
        
        contours, _ = cv2.findContours(thr,1,2)
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
            # 因為 很多程式重複使用 故無法繼續使用舊值
            cX = center_point_x
            cY = center_point_y
        else:
            cX = sumX/sumW  
            cY = sumY/sumW

            # 因為 很多程式重複使用 故無法繼續使用舊值
            # self.last_center = (cX, cY)

        if self.debug:
            ret_thr = thr
            if self.source_path:
                cv2.imshow('Replay', self.frame_new)
                while 1:
                    inn = cv2.waitKey(1)
                    if inn & 0xFF == ord('x'):
                        self._stop = 1
                        break
                    break
        else:
            ret_thr = None
        
        if data == 'x':
            self.feedback_queue.put((0, (center_point_x, center_point_y), (int(cX), center_point_y)))
            return center_point_x - cX
        if data == 'y':
            self.feedback_queue.put((0, (center_point_x, center_point_y), (center_point_x, int(cY))))
            return cY - center_point_y
        if data == 'w':
            return sumW

    def frame_finish(self):
        self.feedback_queue.put('0yaw: {}, roll: {}, pitch: {}'.format(self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output))

    def stop(self):
        self.record.stop_rec()

if __name__ == '__main__':
    try:
        # c = Controller(source_path=0, debug=1, save=0)
        # c = Controller(source_path='video/test1.avi', debug=1, save=0)
        c = Controller(source_path='C:\\Users\\YUMI.Lin\\Desktop\\video\\test8.avi', debug=1, save=1, save_path='C:\\Users\\YUMI.Lin\\Desktop\\testVideo\\')
        print('~~~')
    except Exception as e:
        print(e)
        print('Controller init fail')
        exit()
    c.record.start()
    c.mission_start()
