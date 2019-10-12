from data import MASK, DC
from queue import Queue
from camera import Record
from plane import Plane
from time import time, sleep
from box import Box

import ins, cv2
import numpy as np

delta_c = 0.02

kernel = np.ones((3,3),np.uint8)
kernel2 = np.ones((7,7),np.uint8)

MASK_ALL = np.zeros([240, 320],dtype=np.uint8)
MASK_ALL[0:240, 40:280] = 255

MASK_YAW_UP = np.zeros([240, 320],dtype=np.uint8)
MASK_YAW_UP[0:80, 40:280] = 255

MASK_YAW_DOWN = np.zeros([240, 320],dtype=np.uint8)
MASK_YAW_DOWN[160:240, 40:280] = 255

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

# kernel = np.ones((3,3),np.uint8)  

@ins.only
class Controller():
    def __init__(self, debug=0, replay_path=None, save=1):
        self.frame_queue = Queue(1)
        self.feedback_queue = Queue(1)
        try:
            self.record = Record(self.frame_queue, replay_path=replay_path, save=save, feedback_queue=self.feedback_queue)
            self.box = Box()
        except:
            print('Controller init failed')
            raise IOError

        self.binarized_frame = np.zeros([240, 320],dtype=np.uint8)
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

            self.plane.mc(DC.ALT_HOLD)
            # self.stable(15)
            # self.forward(0, 5)
            self.pitch_test(0, 15)
            self.plane.mc(DC.LOITER)
            # self.stop()
        pass

    def get_frame(self):
        frame = self.frame_queue.get()
        self.frame_new = frame
        self.binarized_frame = self._binarization_general(frame)
        # self.binarized_frame = self._binarization_low_light(frame)
        self.feedback_queue.put(self.binarized_frame)

    def pitch_test(self, pitch, sec=10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            # ret, _, roll, yaw = self._stabilize()
            # ret, pitch_fector, roll, yaw = self._along()
            _, yy, _, thr = self._find_center(self.frame_new, MASK_OWO)
            self.feedback_queue.put(1, 160, yy)

            # pitch_overrided = int(pitch * pitch_fector)
            pitch_overrided = pitch + int((yy - 120) * -1.0)
            self.plane.update(1, pitch_overrided, 0, 0)
            self.fin()


    def forward_exp(self, pitch, sec=10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            # ret, _, roll, yaw = self._stabilize()
            ret, pitch_fector, roll, yaw = self._along()
            _, yy, _, thr = self._find_center(self.frame_new, MASK_OWO)
            self.feedback_queue.put(1, 160, yy)

            pitch_overrided = int(pitch * pitch_fector)
            if yy > 150:
                pitch_overrided += int((yy - 120) * -1.0)
            else:
                pitch_overrided = int(pitch * pitch_fector)

            if self.detect(self.frame_new) == 'R':
                self.box.drop()
                # pitch_overrided = 0
            else:
                self.box.close()
            
            if self.debug:
                print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch_overrided, pitch_fector, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
                if self.replay_path:
                    continue
            # Testing
            # self.plane.update(ret, pitch_overrided, roll, yaw)
            self.plane.update(ret, pitch_overrided, roll, yaw)
            self.fin()

    def forward(self, pitch, sec=10):
        now = time()
        while time()-now<sec:
            self.get_frame()
            # check break condition
            # ret, _, roll, yaw = self._stabilize()
            ret, pitch_fector, roll, yaw = self._along()
            _, yy, _, thr = self._find_center(self.frame_new, MASK_OWO)
            self.feedback_queue.put(1, 160, yy)

            pitch_overrided = int(pitch * pitch_fector)
            # if yy > 150:
            #     pitch_overrided += int((yy - 120) * -1.0)
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
                if self.replay_path:
                    continue
            # Testing
            # self.plane.update(ret, pitch_overrided, roll, yaw)
            self.plane.update(ret, pitch, roll, 0)
            self.fin()

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
            self.fin()


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
        yaw = xx - 160
        self.feedback_queue.put(0, 45, xx)
        xx, _, _, _ = self._find_center(self.frame_new, MASK_LINE_MIDDLE)
        roll = xx - 160
        self.feedback_queue.put(0, 120, xx)
        # pitch_fector = min(50, (50 - abs(yaw))) / max(50, abs(yaw))
        if abs(yaw) > 40:
            # pitch_fector = 0.3
            pitch_fector = 1
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

    def _find_center(self, frame, mask, color='k'):
        thr = self.binarized_frame
        thr = cv2.bitwise_and(thr, thr, mask=mask)
        
        contours, _ = cv2.findContours(thr,1,2)
        sumX=0
        sumY=0
        sumW=0
        # if len(contours) < 5:
        #     self.c -= delta_c
        #     if self.c < 0:
        #         self.c = 0
        # else:
        #     self.c += delta_c

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
            # print('Not found')
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
            # edited = np.copy(thr)
            # edited = cv2.cvtColor(edited, cv2.COLOR_GRAY2BGR)
            # cv2.circle(edited, (int(cX), int(cY)), 5, (178, 0, 192), -1)
            # text_base_position = 140
            # cv2.putText(edited, 'cX: {}'.format(cX), (0, text_base_position), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            # cv2.putText(edited, 'cY: {}'.format(cY), (0, text_base_position+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            # cv2.putText(edited, 'sumW: {}'.format(sumW), (0, text_base_position+40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            # cv2.putText(edited, 'yaw: {}, roll: {}, pitch: {}'.format(self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output), (0, text_base_position+60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            # while self.feedback_queue.full():
            #     try:
            #         self.feedback_queue.get(timeout=0.00001)
            #     except:
            #         pass
            # self.feedback_queue.put(edited)
            if self.replay_path:
                cv2.imshow('Replay', frame)
                # cv2.imshow('Replay', cv2.hconcat([frame, edited]))
                while not cv2.waitKey(0) & 0xFF == ord(' '):
                    sleep(0.1)
        else:
            ret_thr = None
        return cX, cY, sumW, ret_thr

    def fin(self):
        self.feedback_queue.put('yaw: {}, roll: {}, pitch: {}'.format(self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output))

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
