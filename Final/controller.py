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
MASK_FORWARD = (None, 25, 0, 85)
MASK_LINE_MIDDLE = (None, 30, 0, 0)
MASK_LINE_BACKWARD = (None, 25, 0, -85)
MASK_OWO = (40, None, 0, 0)

MAX_MISSION_TIME = 200

def condition(func):
    pass

@only
class Controller():
    def __init__(self, source_path=None, save_path='/home/pi/Desktop/Rhapsody-of-nonsense/records/', save=1, debug=0):
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
        self.light_color = 0
        self.color = 'r'
        self.need_drop = False
        self.dropped = False
        self.global_time = 0

        if not debug:
            try:
                self.plane = Plane()
            except:
                display('Error: Failed to connect plane')
                raise IOError
        elif __name__ == '__main__':
            self.plane = Plane(debug=1)

    def mission_start(self):
        try:
            # self.stop()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            self.plane.update(1, 0, 0, 0)
            # 往前盲走，直到看到紅綠燈
            # self.loop(self.forward_experimental, self.condition_light, sec=30)
            # self.loop(self.forward_no_yaw_experimental, self.condition_light, sec=30)
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, self.condition_light, sec=10)
            # 重設各方向移動，並設定紅綠燈用 PID 值
            self.plane.update(1, 0, 0, 0)
            self.plane.pitch_pid.set_pid(kp=0, ki=0.35, kd=0)
            self.plane.roll_pid.set_windup_guard(40)
            self.loop(self.stable_rad, self.condition_not_red, sec=30)
            # self.loop(self.pause, self.condition_not_red, sec=10)
            if self.light_color == 2:
                self.color = 'g'
            elif self.light_color == 3:
                self.color = 'b'
            else:
                self.color = 'r'
            print('Color:', self.color)
            # 找到燈號，重設 PID 值
            self.plane.pitch_pid.reset()
            self.plane.roll_pid.reset()
            self.plane.update(1, 90, 0, 0)
            # 往前盲走，直到沒看到紅綠燈
            self.loop(self.pause_color, self.condition_no_light, sec=10)
            self.loop(self.pause_color, sec=1.5)
            # 往前移動，看到對應顏色沙包就投下
            self.following(ignore_light=True, drop=True)
            # Work in Progress
            self.following(ignore_light=True)
        except:
            print('Forced stopped')


    def mission_yolo(self):
        """盲走前進 10 秒後降落"""
        try:
            print('Warning -- Yolo strategy')
            # self.stop()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            self.plane.update(1, 0, 0, 0)
            # 往前盲走 10 秒，直接降落
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, sec=10)
        except:
            print('Forced stopped')

    def mission_yolo_2(self):
        """盲走到紅綠燈，等待 15 秒後前進並降落"""
        try:
            print('Warning -- Yolo strategy')
            # self.stop()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            self.plane.update(1, 0, 0, 0)
            # 往前盲走 2 秒，進入紅綠燈區
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, sec=2)
            # 停止 15 秒，等待切換燈號
            self.plane.update(1, 0, 0, 0)
            self.loop(self.pause, sec=15)
            # 往前盲走 3 秒，直接降落
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, sec=3)
        except:
            print('Forced stopped')


    def stop(self):
        raise Exception

    def conditoin_drop(self):
        return self.condition_has_color()

    def condition_not_red(self):
        self.light_color = self.condition_has_light()
        if self.light_color > 1:
            return True

        return False

    def following(self, light_only=False, ignore_light=False, drop=False):
        while True:
            if drop:
                self.loop(self.forward_experimental, self.condition_forward_color, sec=30)
            if light_only:
                self.loop(self.forward_experimental, self.condition_light, sec=30)
            else:
                if ignore_light:
                    self.loop(self.forward_experimental, self.condition_forward, sec=30)
                else:
                    self.loop(self.forward_experimental, self.condition_forward_light, sec=30)
            # self.loop(self.forward, self.forward_condition, sec=30)
            if drop:
                if self.need_drop:
                    self.box.drop()
                    self.dropped = True
                    break

            if not ignore_light:
                if self.light_color:
                    break
            self.plane.update(1, -45, 0, 0)
            self.loop(self.pause, sec=3)

    def condition_forward_color(self):
        if self.condition_find_color() and self.condition_has_color():
            self.need_drop = True
            return True

        if self.condition_forward():
            return True

        
        self.need_drop = False
        return False


    def loop(self, func_loop, func_condition=None, sec=10):
        condition_count = 0
        now = time() 
        while time()-now<sec and self.global_time <= MAX_MISSION_TIME:
            if self.dropped == True:
                self.feedback_queue.put('7===Dropped===')
            self.feedback_queue.put('8===Loop Time: {}==='.format(int(time()-now)))
            self.feedback_queue.put('9===Global Time: {}==='.format(self.global_time))
            if self._stop:
                break
            self._get_frame()
            if func_condition:
                if func_condition():
                    condition_count += 1
                else:
                    condition_count = 0
                
            if condition_count > 10:
                break
            func_loop()
            self.frame_finish()

        self.global_time += int(time()-now)

        
    
    # def pause(self):
    #     self.feedback_queue.put('1PAUSE')

    def pause(self):
        self.feedback_queue.put('1===PAUSE===')

    def pause_color(self):
        self.feedback_queue.put('1===PAUSE, Color: {}==='.format(self.color))

    def pitch_test(self, pitch, sec=10):
        now = time()
        while time()-now<sec:
            self._get_frame()
            self.plane.update(1, pitch, 0, 0)
            self.frame_finish()

    def condition_forward_light(self):
        self.light_color = self.condition_has_light()
        if self.light_color:
            return True

        yaw_weight = self._find_center(mask=MASK_FORWARD, data='w')
        print('yaw weight', yaw_weight)
        if yaw_weight < 10:
            return True

        return False

    def condition_light(self):
        self.light_color = self.condition_has_light()
        if self.light_color:
            return True

        yaw_weight = self._find_center(mask=MASK_FORWARD, data='w')
        print('yaw weight', yaw_weight)
        if yaw_weight < 10:
            global_weight = self._find_center(mask=MASK_ALL, data='w')
            if global_weight < 100:
                return True

        return False

    def condition_no_light(self):
        self.light_color = self.condition_has_light()
        if not self.light_color:
            return True

        return False

    def condition_forward(self):
        yaw_weight = self._find_center(mask=MASK_FORWARD, data='w')
        print('yaw weight', yaw_weight)
        if yaw_weight < 10:
            global_weight = self._find_center(mask=MASK_ALL, data='w')
            if global_weight < 100:
                return True

        return False

    def forward_experimental(self):
        self.feedback_queue.put('1===Forward Experimental===')
        pitch = 70
        # check break condition
        ret, pitch_fector, roll, yaw = self._along_experimental()

        pitch_overrided = int(pitch * pitch_fector)
        
        # if self.debug:
        print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch_overrided, pitch_fector, roll, yaw))
            # print(ret, pitch, roll, yaw, sep='\t')
        # Testing
        # self.plane.update(ret, pitch_overrided, roll, yaw)
        self.plane.update(ret, pitch_overrided, roll, yaw)

    def forward_no_yaw_experimental(self):
        self.feedback_queue.put('1===Forward Experimental (w/o Yaw)===')
        pitch = 70
        # check break condition
        ret, pitch_fector, roll, yaw = self._along_experimental()
        # pitch_ = self._find_center(mask=MASK_OWO, data='y')

        front_weight = self._find_center(mask=MASK_FORWARD, data='w')
        if front_weight < 10:
            # use global center instead
            roll = self._find_center(mask=MASK_ALL, data='x')

        pitch_overrided = int(pitch * pitch_fector)
        
        # if self.debug:
        print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch_overrided, pitch_fector, roll, yaw))
            # print(ret, pitch, roll, yaw, sep='\t')
        # Testing
        # self.plane.update(ret, pitch_overrided, roll, yaw)
        self.plane.update(ret, pitch_overrided, roll, 0)

    def forward_no_yaw(self):
        self.feedback_queue.put('1===Forward No Yaw===')
        pitch = 70
        # check break condition
        # ret, _, roll, yaw = self._stabilize()
        ret, pitch_fector, roll, yaw = self._along_no_yaw()
        pitch_ = self._find_center(mask=MASK_OWO, data='y')

        pitch_overrided = int(pitch * pitch_fector)
        
        # if self.debug:
        print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch_overrided, pitch_fector, roll, yaw))
            # print(ret, pitch, roll, yaw, sep='\t')
        # Testing
        # self.plane.update(ret, pitch_overrided, roll, yaw)
        self.plane.update(ret, pitch_overrided, roll, 0)

    def forward_backup(self, pitch=100, sec=10):
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
            
            # if self.debug:
            print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(ret, pitch_overrided, pitch_fector, roll, yaw))
                # print(ret, pitch, roll, yaw, sep='\t')
            # Testing
            # self.plane.update(ret, pitch_overrided, roll, yaw)
            self.plane.update(ret, pitch_overrided, roll, yaw)
            self.frame_finish()

    def _stabilize(self, color='k'):
        pitch = self._find_center(mask=MASK_OWO, data='y')
        roll = self._find_center(mask=MASK_LINE_MIDDLE, data='x')
        return 1, pitch, roll, 0

    def _along(self, color='k'):
        yaw = self._find_center(mask=MASK_FORWARD, data='x')
        yaw_weight = self._find_center(mask=MASK_FORWARD, data='w')
        # roll = self._find_center(mask=MASK_LINE_MIDDLE, data='x')
        roll = self._find_center(mask=MASK_LINE_BACKWARD, data='x')

        # yaw-roll for parallelity
        yaw_overrided = yaw - roll
        if abs(yaw_overrided) > 40:
            pitch_fector = 0.3
            # pitch_fector = 1
        else:
            pitch_fector = 1

        if yaw_weight < 10:
            pitch_fector = 0.3
            # yaw_overrided = -90
        return 1, pitch_fector, roll, yaw_overrided

    def _along_experimental(self, color='k'):
        front = self._find_center(mask=MASK_FORWARD, data='x')
        front_weight = self._find_center(mask=MASK_FORWARD, data='w')
        # roll = self._find_center(mask=MASK_LINE_MIDDLE, data='x')
        back = self._find_center(mask=MASK_LINE_BACKWARD, data='x')

        # yaw-roll for parallelity
        yaw_overrided = front - back
        roll_overrided = front
        if abs(yaw_overrided) > 40:
            pitch_fector = 0.3
            # pitch_fector = 1
        else:
            pitch_fector = 1

        if front_weight < 10:
            # use global center instead
            pitch_fector = 0.3
            yaw_overrided = self._find_center(mask=MASK_ALL, data='x')

        if yaw_overrided * back == 0:
            yaw_overrided = 0

            # yaw_overrided = -90
        return 1, pitch_fector, roll_overrided, yaw_overrided

    def _along_no_yaw(self, color='k'):
        yaw = self._find_center(mask=MASK_FORWARD, data='x')
        yaw_weight = self._find_center(mask=MASK_FORWARD, data='w')
        roll = self._find_center(mask=MASK_LINE_MIDDLE, data='x')
        # roll = self._find_center(mask=MASK_LINE_BACKWARD, data='x')

        # yaw-roll for parallelity
        yaw_overrided = yaw - roll
        if abs(yaw_overrided) > 40:
            pitch_fector = 0.3
            # pitch_fector = 1
        else:
            pitch_fector = 1

        if yaw_weight < 10:
            pitch_fector = 0.3
            # yaw_overrided = -90
        return 1, pitch_fector, roll, yaw_overrided

    def stable_rad(self):
        self.feedback_queue.put('1===Stable Red===')
        frame = self.frame_new
        r = frame[:,:,2]
        g = frame[:,:,1]
        a = r-g+220
        _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
        pitch = self._find_center(frame=a, mask=MASK_ALL, data='y')
        roll = self._find_center(frame=a, mask=MASK_ALL, data='x')
        self.plane.update(1, pitch, roll, 0)


    def condition_has_light(self):
        """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。"""
        frame = self.frame_new
        r = frame[:,:,2]
        g = frame[:,:,1]
        b = frame[:, :, 0]
        a = r-g+220
        c = b-r+220
        _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
        _, c = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY_INV)
        na = cv2.countNonZero(a)
        nb = cv2.countNonZero(c)

        if na > 5000:
            if na > nb:
                print('R', na, nb)
                return 1
            else:
                print('G', na, nb)
                return 2
        else:
            if nb > 5000:
                print('B', na, nb)
                return 3
            else:
                print('X', na, nb)
                return 0

    def condition_has_color(self):
        hsv = cv2.cvtColor(self.frame_new, cv2.COLOR_BGR2HSV)
        h = hsv[:, :, 0]
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]
        _, s_ = cv2.threshold(s,100,255,cv2.THRESH_BINARY)
        hW = self._find_center((None, None, 0, 0), data='w', frame=s_)
        if hW > 3000:
            return 1
        else:
            return 0
        
    def condition_find_color(self):
        # b100, r180, g54
        hRange=10
        if self.color=='r':
            offset=255
        elif self.color=='g':
            offset=54*255/180
        elif self.color=='b':
            offset=100*255/180
        hsv = cv2.cvtColor(self.frame_new, cv2.COLOR_BGR2HSV)
        h = hsv[:, :, 0]/180*255-offset+hRange
        h = np.asarray(h, np.uint8)
        _, h_ = cv2.threshold(h,2*hRange,255,cv2.THRESH_BINARY_INV)
        hW = self._find_center(mask=(None, 50, 0, 0), data='w', frame=h_)
        # hW = self._find_center(mask=(50, 50, 0, 0), data='w', frame=h_)
        # print(hW)
        if hW > 3000:
            return 1
        else:
            return 0


    def _get_frame(self):
        frame = self.frame_queue.get()
        self.binarized_frame = self._binarization_general(frame)
        # self.binarized_frame = self._binarization_low_light(frame)
        self.feedback_queue.put(self.binarized_frame)

    def _binarization_general(self, frame):
        frame = cv2.GaussianBlur(frame, (13, 13), 0)
        self.frame_new = frame
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

    def _mask(self, frame=None, mask=(None, None, 0, 0), img_size=IMAGE_SIZE):
        """mask -> (width, hight, offset_x, offset_y),width and hight are half value
        """
        if type(frame) is not np.ndarray:
            frame = self.binarized_frame
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
        masked = np.bitwise_and(frame, mask)
        return masked

    def _find_center(self, mask, data, frame=None, error_num=10):
        "mask: (width, hight, offset_x, offset_y),\ndata: 'x', 'y', 'w'"
        thr =self._mask(frame=frame, mask=mask)

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
            return cX - center_point_x
        if data == 'y':
            self.feedback_queue.put((0, (center_point_x, center_point_y), (center_point_x, int(cY))))
            return center_point_y - cY
        if data == 'w':
            return sumW

    def frame_finish(self):
        self.feedback_queue.put('0yaw: {:>6d}, roll: {:>6d}, pitch: {:>6d}, color: {}'.format(self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output, self.color))

    def stop(self):
        self.record.stop_rec()

if __name__ == '__main__':
    try:
        # c = Controller(source_path=0, debug=1, save=0)
        c = Controller(source_path=2, debug=1, save=1, save_path='videooutput/')
        # c = Controller(source_path='C:\\Users\\YUMI.Lin\\Desktop\\video\\test8.avi', debug=1, save=1, save_path='C:\\Users\\YUMI.Lin\\Desktop\\testVideo\\')
        print('~~~')
    except Exception as e:
        print(e)
        print('Controller init fail')
        exit()
    c.record.start()
    c.mission_start()
