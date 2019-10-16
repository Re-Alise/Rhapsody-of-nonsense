from data import MASK
from queue import Queue
from camera import Record
from plane import Plane
from time import time, sleep
from tool import *
from box import Box

import numpy as np
import cv2


# ==========Ultra Important Things==========
hue_floor = 24
light_threshold = 100
na_offset = 220
nb_offset = 200

# ==========================================
delta_c = 0.03
C_START = 3.5

kernel = np.ones((3, 3), np.uint8)
kernel2 = np.ones((7, 7), np.uint8)
IMAGE_SIZE = (240, 320)  # 高寬

# MASK: width, hight, offset_x, offset_y
#       (half) (half) (right+)  (top+)
MASK_ALL = (None, None, 0, 0)
MASK_YAW_UP = (120, 40, 0, 80)
MASK_YAW_DOWN = (120, 40, 0, -80)
MASK_FORWARD = (None, 25, 0, 85)
MASK_LINE_MIDDLE = (None, 30, 0, 0)
MASK_LINE_BACKWARD = (None, 25, 0, -85)
MASK_OWO = (40, None, 0, 0)
MASK_MIDDLE = (50, None, 0, 0)
MASK_UP = (None, 60, 0, 60)
MASK_DOWN = (None, 60, 0, -60)

MAX_MISSION_TIME = 170

# ============= From funcs =================
# IMAGE_SIZE = (320, 240)
path = ""
path = "./../video/"
# path = "C:\\Users\\YUMI.Lin\\Desktop\\video\\"
# fileName = "radline.avi"
fileName = "test8.avi"
gaussian = (13, 13)
kernel = np.ones((3,3),np.uint8)
# adjust = 0

# select = 0
# display = 0
# show_num = 6


# target_color = 0
# step = -1


# PARAMETER
normal_offset = 180
normal_threshold = 100
gray_threshold = 100
saturation_threshold = 145
hue_range = 20
hue_threshold = 2*hue_range
hue_red = 180 # use overfloat value don't use value like 1, 0, 5 etc..
hue_green = 90
hue_blue = 120

default_drop_color = 3
default_land_color = 2


# 條件
na_min = 4000
nb_min = 4000
drop_min = 20000
has_color_min = 10000
has_finishline_min = 1000
big_red_min = drop_min
big_color_min = 20000
floor_forward_min = 10
floor_min = 100

# MASK
MASK_FORWARD = (None, 25, 0, 85)
MASK_DROP = (None, 60, 0, 0)


# ==========================================


def condition(func):
    pass


@only
class Controller():
    def __init__(self, source_path=None, save_path='/home/pi/Desktop/Rhapsody-of-nonsense/records/', save=1, debug=0):
        """debug: manual read video (" ", "x"), and no use PIGPIO"""
        self.debug = debug
        self.frame_queue = Queue(1)
        self.feedback_queue = Queue()
        self.record = Record(self.frame_queue, debug=self.debug, feedback_queue=self.feedback_queue,
                             source_path=source_path, save=save, save_path=save_path)
        self.source_path = source_path
        self.frame_new = None
        self.c = C_START
        self._stop = 0
        self.box = Box()
        self.light_color = 0
        self.color = 1
        self.need_drop = False
        self.dropped = False
        self.global_time = 0
        self.binarization_state = 0
        self.need_pause = False
        self.start_time = 0

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
            self.start_time = time()
            # normal:0, light:1, color:2
            # self.halt()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            print('=' * 20 + '前往紅綠燈')
            self.binarization_state = 0
            # self.plane.update(1, 0, 0, 0)
            # 往前盲走，直到看到紅綠燈
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, self.condition_light, sec=10)
            # 重設各方向移動，並設定紅綠燈用 PID 值
            print('=' * 20 + '定在紅綠燈')
            self.binarization_state = 1
            # self.plane.update(1, 0, 0, 0)
            self.plane.pitch_pid.set_pid(kp=0, ki=0.35, kd=0)
            self.plane.roll_pid.set_windup_guard(40)
            self.loop(self.stable_red, self.condition_not_red, sec=30)
            # self.loop(self.pause, self.condition_not_red, sec=15)
            if self.light_color == 2:
                self.color = 2
            elif self.light_color == 3:
                self.color = 3
            else:
                self.color = 3
            print('=' * 20 + 'Color:', self.color)
            # 找到燈號，重設 PID 值
            self.binarization_state = 0
            self.plane.pitch_pid.reset()
            self.plane.roll_pid.reset()
            print('=' * 20 + '盲走')
            # 往前盲走，直到沒看到紅綠燈
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, self.condition_no_light, sec=10)
            self.loop(self.pause, sec=1.5)
            # 往前移動，直到看到大色塊（地毯）
            print('=' * 20 + '轉彎到色塊前')
            self.following(condition=self.condition_forward_has_color)
            # self.loop(self.forward, self.condition_has_color, sec=30)
            # 往前移動，看到對應顏色或找不到色塊，沙包就投下
            self.binarization_state = 2
            print('=' * 20 + '前進丟沙包')
            self.following(drop=True, yaw=False)
            self.following(yaw=False, condition=self.condition_no_drop_color)
            self.box.drop()
            self.binarization_state = 0
            # 走到看見終點線
            self.loop(self.forward, self.condition_all_floor, cond2=detect_finishline, sec=30)
            # 盲走直到看見紅色
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, self.condition_has_big_red, sec=10)
            # 繞圈直到看見目標
            self.loop(self.around, self.condition_has_target_color, sec=10)
            # 飛過去
            self.loop(self.stable, sec=7)

            # self.following(ignore_light=True)
        except:
            print('=' * 20 + 'Forced stopped')

    def mission_start_alternative(self):
        try:
            self.start_time = time()
            # normal:0, light:1, color:2
            # self.halt()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            print('=' * 20 + '前往紅綠燈')
            self.binarization_state = 0
            # self.plane.update(1, 0, 0, 0)
            # 往前盲走，直到看到紅綠燈
            # self.plane.update(1, 90, 0, 0)
            self.loop(self.forward_no_yaw, self.condition_light, sec=10)
            # 重設各方向移動，並設定紅綠燈用 PID 值
            print('=' * 20 + '定在紅綠燈')
            self.binarization_state = 1
            # self.plane.update(1, 0, 0, 0)
            self.plane.pitch_pid.set_pid(kp=0, ki=0.35, kd=0)
            self.plane.roll_pid.set_windup_guard(40)
            self.loop(self.stable_red, self.condition_not_red, sec=30)
            # self.loop(self.pause, self.condition_not_red, sec=15)
            if self.light_color == 2:
                self.color = 2
            elif self.light_color == 3:
                self.color = 3
            else:
                self.color = 3
            print('=' * 20 + 'Color:', self.color)
            # 找到燈號，重設 PID 值
            self.binarization_state = 0
            self.plane.pitch_pid.reset()
            self.plane.roll_pid.reset()
            print('=' * 20 + '盲走')
            # 往前盲走，直到沒看到紅綠燈
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, self.condition_no_light, sec=10)
            self.loop(self.pause, sec=1.5)
            # 往前移動，直到看到大色塊（地毯）
            print('=' * 20 + '轉彎到色塊前')
            self.following(condition=self.condition_forward_has_color)
            # self.loop(self.forward, self.condition_has_color, sec=30)
            # 往前移動，看到對應顏色或找不到色塊，沙包就投下
            self.binarization_state = 2
            print('=' * 20 + '前進丟沙包')
            self.following(drop=True, yaw=False)
            self.following(yaw=False, condition=self.condition_no_drop_color)
            self.box.drop()
            self.binarization_state = 0
            self.loop(self.forward, self.condition_all_floor, sec=6)

            # self.following(ignore_light=True)
        except:
            print('=' * 20 + 'Forced stopped')

    def mission_yolo_1(self):
        """盲走前進 10 秒後降落"""
        try:
            self.start_time = time()
            print('Warning -- Yolo strategy 1')
            # self.halt()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            # self.plane.update(1, 0, 0, 0)
            # 往前盲走 10 秒，直接降落
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, sec=10)
        except:
            print('Forced stopped')

    def mission_yolo_2(self):
        """盲走到紅綠燈，等待 15 秒後前進並降落"""
        try:
            self.start_time = time()
            print('Warning -- Yolo strategy 2')
            # self.halt()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            # self.plane.update(1, 0, 0, 0)
            # 往前盲走 2 秒，進入紅綠燈區
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, sec=2)
            # 停止 15 秒，等待切換燈號
            # self.plane.update(1, 0, 0, 0)
            self.loop(self.pause, sec=15)
            # 往前盲走 3 秒，直接降落
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, sec=3)
        except:
            print('Forced stopped')

    def mission_yolo_3(self):
        """走到紅綠燈，等待燈號變色後前進並降落"""
        try:
            self.start_time = time()
            print('Warning -- Yolo strategy 3')
            # self.halt()
            # all mission fun return "ret, pitch, roll, yaw"
            # 起飛、機身已穩定五秒裝，重設各方向移動
            print('=' * 20 + '前往紅綠燈')
            self.binarization_state = 0
            # self.plane.update(1, 0, 0, 0)
            # 往前盲走，直到看到紅綠燈
            self.plane.update(1, 90, 0, 0)
            self.loop(self.pause, self.condition_light, sec=10)

            # 延遲一秒，確認在紅綠燈上
            self.plane.update(1, 70, 0, 0)
            self.loop(self.pause, sec=1)

            # 等待紅綠燈變色
            # self.plane.update(1, 0, 0, 0)
            self.binarization_state = 1
            self.loop(self.pause, self.condition_not_red, sec=30)
            # self.loop(self.pause, self.condition_not_red, sec=15)
            if self.light_color == 2:
                self.color = 2
            elif self.light_color == 3:
                self.color = 3
            else:
                self.color = 3
            print('=' * 20 + 'Color:', self.color)

            # 前進五秒，然後降落
            self.plane.update(1, 70, 0, 0)
            self.loop(self.pause, sec=5)
        except:
            print('Forced stopped')

    def halt(self):
        raise Exception

    def condition_all_floor(self):
        floor_bin = self.get_hue_binarized(hue_floor, invert=1)
        floor_bin_forward = self._mask(floor_bin, MASK_FORWARD)
        if self.get_weight(floor_bin) < floor_forward_min:
            if self.get_weight(floor_bin_forward) < floor_min:
                self.need_pause = True
                return 1
        
        # if self.fin

        self.need_pause = False
        return 0

    def condition_forward_has_color(self):
        if self.condition_has_color() or self.condition_all_floor():
            return True

        return False

    def condition_has_color(self):
        s_ = self.get_saturation_binarized()
        s__ = self._mask(s_, (None, 80, 0, 40))
        # s_ = cv2.cvtColor(s_, cv2.COLOR_GRAY2BGR)
        ns = self.get_weight(s__)
        if ns > has_color_min:
            return 1
        else:
            return 0

    def condition_has_drop_color(self):
        saturation_binarized = self.get_saturation_binarized()
        saturation_binarized = self._mask(saturation_binarized, MASK_DROP)
        green_hue_binarized = self.get_hue_binarized(hue_green)
        green_binarized = self.bin_and(saturation_binarized, green_hue_binarized)
        if self.get_weight(green_binarized) > drop_min:
            return 1
        if self.color == 3:
            blue_hue_binarized = self.get_hue_binarized(hue_blue)
            blue_binarized = self.bin_and(saturation_binarized, blue_hue_binarized)
            if self.get_weight(blue_binarized) > drop_min:
                return 1
        return 0

    def condition_has_big_red(self):
        s_ = self.get_saturation_binarized()
        red_ = self.get_hue_binarized(hue=hue_red)
        red = self.bin_and(s_, red_)
        if self._find_center(frame=red, mask=MASK_ALL, data='w')>20000:
            return 1
        return 0

    def condition_has_target_color(self):
        target = self.target_map()
        if self._find_center(frame=target, mask=MASK_ALL, data='w')>8000:
            return 1
        return 0

    def following(self, drop=False, condition=None, yaw=True):
        if yaw:
            task = self.forward
        else:
            task = self.forward_no_yaw
        while True:
            if drop:
                if condition:
                    self.loop(task, condition, sec=30)
                else:
                    self.loop(task, self.condition_forward_color, sec=30)
            else:
                if condition:
                    self.loop(task, condition, sec=30)
                else:
                    self.loop(task, self.condition_all_floor, sec=30)
            # self.loop(self.forward, self.forward_condition, sec=30)
            if drop:
                if self.need_drop:
                    self.box.drop()
                    self.dropped = True
                    break
            
            if self.need_pause == False:
                break

            self.plane.update(1, -45, 0, 0)
            self.loop(self.pause, sec=3)

    def condition_no_drop_color(self):
        if not self.condition_has_color():
            return True

        return False

    def condition_forward_color(self):
        if self.condition_has_color() and self.condition_has_drop_color():
            self.need_drop = True
            return True
        else:
            self.need_drop = False

        if not self.condition_has_color():
            self.need_drop = True
            return True
        else:
            self.need_drop = False

        if self.condition_all_floor():
            return True

        return False

    def loop(self, func_loop, func_condition=None, cond2=None, sec=10):
        condition_count = 0
        now = time()
        self.need_pause = False
        while time()-now < sec:
            self._get_frame()
            if self.global_time > MAX_MISSION_TIME:
                print('=========== Time Out ===========')
                break
            if self.dropped == True:
                self.feedback_queue.put('7===Dropped===')
            self.feedback_queue.put(
                '8===Loop Time: {}==='.format(int(time()-now)))
            self.global_time = time() - self.start_time
            self.feedback_queue.put(
                '9===Global Time: {}==='.format(int(self.global_time)))
            if self._stop:
                break
            if func_condition:
                if func_condition():
                    condition_count += 1
                elif cond2:
                    if cond2():
                        condition_count += 1
                else:
                    condition_count = 0
                


            if condition_count > 10:
                break
            func_loop()
            self.frame_finish()


    def pause(self):
        self.feedback_queue.put('1===PAUSE===')

    def condition_forward_light(self):
        self.light_color = self.detect_light()
        if self.light_color:
            return True

        yaw_weight = self._find_center(mask=MASK_FORWARD, data='w')
        print('yaw weight', yaw_weight)
        if yaw_weight < 10:
            return True

        return False

    def condition_not_red(self):
        """偵測紅綠燈，且非紅色的相同顏色"""
        color = self.detect_light()
        if color == self.light_color and color > 1:
            return True
        else:
            self.light_color = color
            return False


    def condition_light(self):
        """偵測紅綠燈，且相同顏色"""
        # self.light_color = self.detect_light()
        color = self.detect_light()
        if color == self.light_color and color > 0:
            return True
        else:
            self.light_color = color
            return False

    def condition_no_light(self):
        """偵測直到看不到紅綠燈"""
        color = self.detect_light()
        if color == 0:
            return True

        return False

    def forward(self):
        self.feedback_queue.put('1===Forward Experimental===')
        pitch = 70
        ret, pitch_fector, roll, yaw = self._along_experimental()

        pitch_overrided = int(pitch * pitch_fector)

        # print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(
        #     ret, pitch_overrided, pitch_fector, roll, yaw))
        self.plane.update(ret, pitch_overrided, roll, yaw)

    def forward_no_yaw(self):
        self.feedback_queue.put('1===Forward Experimental (w/o Yaw)===')
        pitch = 70
        ret, pitch_fector, roll, yaw = self._along_experimental()
        # pitch_ = self._find_center(mask=MASK_OWO, data='y')

        front_weight = self._find_center(mask=MASK_FORWARD, data='w')
        if front_weight < 10:
            # use global center instead
            roll = self._find_center(mask=MASK_ALL, data='x')

        pitch_overrided = int(pitch * pitch_fector)

        # print('ret: {}\t pitch overrided: {}\t pitch fector: {}\t roll: {}\t yaw: {}'.format(
        #     ret, pitch_overrided, pitch_fector, roll, yaw))
        self.plane.update(ret, pitch_overrided, roll, 0)

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

    def stable_red(self):
        self.feedback_queue.put('1===Stable Red===')
        frame = self.frame_new
        r = frame[:, :, 2]
        g = frame[:, :, 1]
        a = r-g+220
        _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
        pitch = self._find_center(frame=a, mask=MASK_ALL, data='y')
        roll = self._find_center(frame=a, mask=MASK_ALL, data='x')
        self.plane.update(1, pitch, roll, 0)

    def stable_target(self):
        target = self.target_map()
        self.feedback_queue.put('1===Stable {}==='.format(self.color))
        pitch = self._find_center(frame=target, mask=MASK_ALL, data='y')
        roll = self._find_center(frame=target, mask=MASK_ALL, data='x')
        self.plane.update(1, pitch, roll, 0)

    def around(self, bined):
        self.feedback_queue.put('1===around Red===')
        pitch = 65
        roll = self._find_center(frame=bined, mask=MASK_MIDDLE, data='x')
        yaw1 = self._find_center(frame=bined, mask=MASK_UP, data='x')
        yaw2 = self._find_center(frame=bined, mask=MASK_DOWN, data='x')
        self.plane.update(1, pitch, roll, yaw1-yaw2)

    def detect_finishline(self):
        red = self.get_hue_binarized(hue=hue_red)
        nh = cv2.countNonZero(red)
        if nh>has_finishline_min:
            return 1
        else:
            return 0

    def detect_light(self):
        """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。
        R na>>nb
        G na~~nb
        B na<<nb
        
        """
        frame = self.frame_new
        r = frame[:,:,2]
        g = frame[:,:,1]
        b = frame[:, :, 0]
        a = r-g+ na_offset
        c = b-r+ nb_offset
        ans = cv2.hconcat([a, c])
        ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
        ans = cv2.hconcat([frame, ans])
        _, a = cv2.threshold(a, light_threshold, 255, cv2.THRESH_BINARY_INV)
        _, c = cv2.threshold(c, light_threshold, 255, cv2.THRESH_BINARY_INV)
        na = cv2.countNonZero(a)
        nb = cv2.countNonZero(c)
        ab = na/nb if nb else 999
        ba = nb/na if na else 999
        if na > na_min or nb > nb_min:
            if ab>30:
                print('R', na, nb)
                return 1
            elif ba>30:
                print('B', na, nb)
                return 3
            else:
                print('G', na, nb)
                return 2
        else:
            print('X', na, nb)
            return 0


    def _get_frame(self):
        frame = self.frame_queue.get()
        self.binarized_frame = self._binarization_general(frame)
        self.feedback_queue.put(self.binarized_frame)

    def _binarization_general(self, frame):
        frame = cv2.GaussianBlur(frame, (13, 13), 0)
        self.frame_new = frame

        if self.binarization_state == 0:
            binarized_frame = self.normal_map(frame)
        elif self.binarization_state == 1:
            binarized_frame = self.light_map(frame)
        elif self.binarization_state == 2:
            binarized_frame = self.color_map(frame)
        else:
            print('invalid binarization state')
            binarized_frame = self.normal_map(frame)
        return binarized_frame

    def _mask(self, frame=None, mask=(None, None, 0, 0), img_size=IMAGE_SIZE):
        """mask -> (width, hight, offset_x, offset_y),width and hight are half value
        """
        if type(frame) is not np.ndarray:
            frame = self.binarized_frame
        width, hight, offset_x, offset_y = mask
        mask = np.zeros(img_size, dtype=np.uint8)
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

        mask[y1:y2, x1:x2] = 255
        self.feedback_queue.put((1, (x1, y1), (x2, y2)))
        masked = self.bin_and(frame, mask)
        return masked

    def _find_center(self, mask, data, frame=None, error_num=10):
        "mask: (width, hight, offset_x, offset_y),\ndata: 'x', 'y', 'w'"
        thr = self._mask(frame=frame, mask=mask)

        center_point_x = IMAGE_SIZE[1]//2 + mask[2]
        center_point_y = IMAGE_SIZE[0]//2 - mask[3]
        sumX = 0
        sumY = 0
        sumW = 0

        contours, _ = cv2.findContours(thr, 1, 2)
        if len(contours) < error_num:
            self.c -= delta_c
            if self.c < 0:
                self.c = 0
        else:
            self.c += delta_c

        for cnt in contours:
            M = cv2.moments(cnt)
            if M['m00'] < 100:
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
            self.feedback_queue.put(
                (0, (center_point_x, center_point_y), (int(cX), center_point_y)))
            return cX - center_point_x
        if data == 'y':
            self.feedback_queue.put(
                (0, (center_point_x, center_point_y), (center_point_x, int(cY))))
            return center_point_y - cY
        if data == 'w':
            return sumW
    
    def normal_map(self, frame):
        # frame = cv2.GaussianBlur(frame, gaussian, 0)
        r = frame[:,:,2]
        b = frame[:, :, 0]
        c = b-r+ normal_offset
        # _, c_ = cv2.threshold(c, normal_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
        _, c_ = cv2.threshold(c, normal_threshold, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # c_ = cv2.cvtColor(c_, cv2.COLOR_GRAY2BGR)
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # _, gray_ = cv2.threshold(gray, gray_threshold, 255, cv2.THRESH_BINARY_INV +cv2.THRESH_OTSU)
        # binarized_frame = np.bitwise_and(c_, gray_)
        binarized_frame = c_
        return binarized_frame

    def light_map(self, frame):
        # frame = cv2.GaussianBlur(frame, gaussian, 0)
        r = frame[:,:,2]
        g = frame[:,:,1]
        a = r-g+ na_offset
        _, a_ = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
        return a_

    def color_map(self, frame):
        # frame = cv2.GaussianBlur(frame, gaussian, 0)
        s_ = self.get_saturation_binarized()
        return s_

    def red_map(self):
        s_ = self.get_saturation_binarized()
        red_ = self.get_hue_binarized(hue = hue_red)
        red = self.bin_and(s_, red_)
        return red
    
    def target_map(self):
        s_ = self.get_saturation_binarized()
        if self.color == 3:
            hue = hue_blue
        else:
            hue = hue_green
        target_ = self.get_hue_binarized(hue=hue)
        target = self.bin_and(s_, target_)
        return target

    def get_hue_binarized(self, hue=180, invert=0):
        hsv = cv2.cvtColor(self.frame_new, cv2.COLOR_BGR2HSV)
        h = hsv[:, :, 0]/180*255-int((hue-hue_range)/180*255)
        h = np.asarray(h, np.uint8)
        if invert:
            _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
        else:
            _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
        return h_

    def get_saturation_binarized(self):
        hsv = cv2.cvtColor(self.frame_new, cv2.COLOR_BGR2HSV)
        s = hsv[:, :, 1]
        _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
        return s_

    def get_weight(self, bined):
        return cv2.countNonZero(bined)

    def bin_and(self, frame1, frame2):
        return np.bitwise_and(frame1, frame2)

    def bin_or(self, frame1, frame2):
        return np.bitwise_or(frame1, frame2)

    def frame_finish(self):
        self.feedback_queue.put('0yaw: {:>6d}, roll: {:>6d}, pitch: {:>6d}, color: {}'.format(
            self.plane.yaw_pid.output, self.plane.roll_pid.output, self.plane.pitch_pid.output, self.color))

    def stop(self):
        self.record.stop_rec()


if __name__ == '__main__':
    try:
        # c = Controller(source_path=0, debug=1, save=0)
        # c = Controller(source_path=2, debug=1, save=1,
        #                save_path='videooutput/')
        c = Controller(source_path='./../video/test5.avi', debug=1, save=1, save_path='testout/')
        print('~~~')
    except Exception as e:
        print(e)
        print('Controller init fail')
        exit()
    c.record.start()
    c.mission_start()
