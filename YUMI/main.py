from time import time, sleep
from ppm import PPM
from threading import Thread
from queue import Queue
from ins import get_only
from enum import IntEnum

import numpy as np
import cv2
import pigpio

TAKEOFF_SPEED = 22
LAND_SPEED = 18
NORMAL_SPEED = 10


# cv2 const
ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

LINE_THRESHOLD = (96, 96, 96)
BLUR_PIXEL = (5, 5)
CONTOUR_COLOR = (0, 255, 64) #BGR
CENTROID_COLOR = (0, 0, 255)  # BGR

MASK_ALL = np.zeros([240, 320],dtype=np.uint8)
MASK_ALL[0:240, 0:320] = 255

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

speed = 1
adjust = 1

"""
標準流程
較正時脈
ARM
起飛    快速拉高
穩定    定位在圓圈上方 盡量穩定
循線    沿線走
停止線  找到線 停在前面
等帶顏色轉變
循線    沿線走
找到色塊    
(懸停)
投放
循線
找到紅線
找到目標
穩定
降落
DISARM
------------------------------------------
核心: 循線、繞色塊、穩色塊
"""
# maybe also be a pid-controller
class Controller(Thread):
    """PPM output controller powered by pigpio

    **Start the pigpio daemon before running: sudo pigpiod**

    Arguments:
    input_queue -- Queue to trans
    gpio -- Number of output pin, equivalent to GPIO.BCM (GPIOX)
    channel -- Number of PPM channel (8 default)
    frame_ms -- Time interval between frames in microsecond (5 minimum, 20 default)

    Source: https://www.raspberrypi.org/forums/viewtopic.php?t=219531
    """

    def __init__(self, input_queue, gpio, channels=8, frame_ms=20):
        Thread.__init__(self)
        self._input_queue = input_queue
        self._gpio = gpio
        self._channels = channels
        self._pi = get_only(pigpio.pi)

        if not self._pi.connected:
            print('Error: pigpio is not initialized')
            exit(0)

        self._ppm = PPM(self._pi, self._gpio, channels=channels, frame_ms=frame_ms)
        # Default output signal for stablizing
        self._ppm.update_channels([1500, 1500, 1100, 1500, 1500, 1500, 1500, 1500])
        self.daemon = 1
        self.start()

    def run(self):
        while 1:
            signals = self._input_queue.get()
            self._ppm.update_assign(signals)

class Sonic():
    def __init__(self, pi, trigger_pin=19, echo_pin=26):
        print('sonic init')
        self._pi = pi
        pi.callback(echo_pin, pigpio.EITHER_EDGE, self.dealt)
        self.value = 0
        self.time_rise = 0
        self.values = [0, 0, 0, 0, 0]
        self.index = 0
        # wf = []
        # wf.append(pigpio.pulse(1 << trigger_pin, 0, 10))
        # wf.append(pigpio.pulse(0, 1 << trigger_pin, 40*1000-10))
        # pi.wave_clear()

        # pi.wave_add_generic(wf)
        # wid = pi.wave_create()
        # pi.wave_send_repeat(wid)

    def dealt(self, gpio, level, tick):
        if level == 1: # rising
            self.time_rise = tick
            # self.num1+=1
        elif level == 0: # falling
        # if self.num
            passTime = tick-self.time_rise
            if passTime < 25000:
                self.value = passTime*.017150


    def run(self):
        while 1:
            sleep(.033)
            self._pi.write(19, 1)
            sleep(.00001)
            self._pi.write(19, 0)
    
    def test(self, sec=10):
        now = time()
        times = 0
        while time()-now < sec:
            times+=1
            sleep(.1)
            print('value:', self.value)
        print(times)
        input('')
        
class DC(IntEnum):
        PITCH = 0
        ROLL = 1
        THROTTLE = 2
        YAW = 3
        MODE = 5
        AUTO = 6

class Plane():
    """main program
    """

    def __init__(self):
        # just one buffer because we just need the last value
        self.output_queue = Queue(1)
        # self.cap = cv2.VideoCapture(0)
        self._pi = get_only(pigpio.pi)
        self._pi.wave_tx_stop()
        self.sonic = Sonic(self._pi)
        self.hight = 130
        Controller(self.output_queue, 13)

    def regulate(self):
        pass

    def arm(self):
        sleep(0.1)
        self.output([(DroneControl.THROTTLE, -50), (DroneControl.YAW, 50)]) # set throttle to lowest, yaw to right
        sleep(2)
        self.output([(DroneControl.THROTTLE, 0)])

    def predealt(self):
        """幫邊緣做偏移
        """

    def take_off(self):
        """依靠超音波 去起飛
        """
        self.output([(DroneControl.PITCH, 0), (DroneControl.ROLL, 0), (DroneControl.THROTTLE, 5), (DroneControl.YAW, 0)])
        while 1:
            if self.sonic.value>100:
                break
        self.output([(DroneControl.THROTTLE, 0)])

    def throttle_test(self):
        self.output([(DroneControl.THROTTLE, 0)])
        sleep(0.1)
        self.output([(DroneControl.THROTTLE, -50)])

    def land(self):
        self.output([(DroneControl.PITCH, 0), (DroneControl.ROLL, 0), (DroneControl.THROTTLE, -5), (DroneControl.YAW, 0),])
        while 1:
            self.sonic.start()
            self.sonic.join()
            if self.sonic.value<5:
                self.output([(DroneControl.THROTTLE, -50),])
                break

    def disarm(self):
        self.output([(DroneControl.THROTTLE, -50), (DroneControl.YAW, -50)]) # set throttle to lowest, yaw to lift
        sleep(5)
        self.output([(DroneControl.YAW, 0)])

    def auto(self):
        n = self._pi.read(6)
        return n

    def _stabilize(self, frame, color):
        xx, yy, _ = self._find_center(frame, MASK_ALL)
        pitch = 120-yy
        row = xx-160
        self.output([()])

    def _along(self, frame, color):
        xx, _, _ = self._find_center(frame, MASK_FORWARD)
        yaw = xx-160
        _, yy, _ = self._find_center(frame, MASK_LINE_MIDDLE)
        row = 120-yy
        pass

    def _around(self, frame, color):
        _, yy, _ = self._find_center(frame, MASK_RIGHT)
        row = 120-yy
        _, _, w1 = self._find_center(frame, MASK_TOP)
        _, _, w2 = self._find_center(frame, MASK_BUTTON)
        yaw = w1-w2
        pass

    def _detect(self, frame):
        _, _, ww = self._find_center(frame, MASK_ALL)
        if ww > self.something:
            return 1
        else:
            return 0

    def _chech_hight(self):
        pass

    def _find_center(self, frame, mask):
        frame = cv2.bitwise_and(frame, frame, mask=mask)
        contours, _ = cv2.findContours(frame,1,2)
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
        cX = int(sumX/sumW)
        cY = int(sumY/sumW)
        return cX, cY, sumW

    def output(self, *arg, **kws):
        while self.output_queue.full():
            try:
                self.output_queue.get(timeout=0.00001)
            except:
                pass
        self.output_queue.put(*arg, **kws)

if __name__ == '__main__':
    # ----------------------------------------------
    pp = pigpio.pi()
    plane = Plane()
    mode_auto = pp.read(6)
    # test the sonic
    plane.sonic.test()

    print('init finish-------------------------------')
    # while 1:
    #     start_signal = pp.read(6)
    #     if start_signal and not mode_auto:
    #         # auto run
    #         print('autoMode')
    #         mode_auto = 1
    #         sleep(.1)
    #         plane.arm()
    #         sleep(.1)
    #         plane.throttle_test()
    #         sleep(.1)
    #         plane.disarm()
    #         print('mission completed')
    #         pass
    #     else:
    #         if not start_signal:
    #             mode_auto = 0
    #     print(start_signal)
    #     sleep(.1)
