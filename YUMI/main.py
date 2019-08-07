from time import time, sleep
# from ppm import PPM
from threading import Thread
from queue import Queue
from ins import get_only
import numpy as np
import cv2

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
        # self._pi = get_only(pigpio.pi)

        # if not self._pi.connected:
        #     print('Error: pigpio is not initialized')
        #     exit(0)

        # self._pi.wave_tx_stop()  # Start with a clean slate.
        # self._ppm = PPM(self._pi, self._gpio, channels=channels, frame_ms=frame_ms)
        # Default output signal for stablizing
        # self._ppm.update_channels([1500, 1500, 1100, 1500, 1500, 1500, 1500, 1500])
        self.daemon = 1
        self.start()

    def run(self):
        while 1:
            signals = self._input_queue.get()
            # self._ppm.update_assign(signals)

class Sonic(Thread):
    def __init__(self, trigger_pin, echo_pin):
        Thread.__init__(self)
        # self._pi = get_only(pigpio.pi)
        self.trigger = trigger_pin
        self.echo = echo_pin
        self.daemon = 1
        self.value = 0

    def run(self):
        # self._pi.write(self.trigger, 1)
        # sleep(0.00001)
        # self._pi.write(self.trigger, 0)
        # while self._pi.read(self.echo) == 0:
        #     pass
        # startTime = time()
        # while self._pi.read(self.echo) == 1:
        #     pass
        # passTime = time()-startTime
        # self.value = passTime*17150
        pass

class Plane():
    """main program
    """
    def __init__(self):
        # just one buffer because we just need the last value
        self.output_queue = Queue(1)
        self.cap = cv2.VideoCapture(0)
        self.sonic = get_only(Sonic, 37, 35)
        # self._pi = get_only(pigpio.pi)
        Controller(self.output_queue, 6)

        # 校正時脈
        self.regulate()

    def regulate(self):
        pass

    def arm(self):
        sleep(0.1)
        self.output([(2, 1100), (3, 1900)]) # set throttle to lowest, yaw to right
        sleep(2)
        self.output([(3, 1500), ()])

    def predealt(self):
        """幫邊緣做偏移
        """

    def take_off(self):
        """依靠超音波 去起飛
        """
        self.output([(0, 1500), (1, 1500), (2, 1620), (3, 1500)])
        while 1:
            self.sonic.start()
            self.sonic.join()
            if self.sonic.value>100:
                break
        self.output([(2, 1500)])

    def throttle_test(self):
        self.output([(2, 1500)])
        sleep(0.1)
        self.output([(2, 1100)])

    def land(self):
        self.output([(0, 1500), (1, 1500), (2, 1410), (3, 1500),])
        while 1:
            self.sonic.start()
            self.sonic.join()
            if self.sonic.value<5:
                self.output([(2, 1100), ()])
                break

    def disarm(self):
        self.output([(2, 1100), (3, 1100)]) # set throttle to lowest, yaw to lift
        sleep(5)
        self.output([(3, 1500)])

    def auto(self, frame, fun=0):
        pass
        # the main

    def _stabilize(self, frame):
        pass
        # xx, yy = self._find_center_error(frame, MASK_POS)
        # self.output([(0, 1500+10*(160-xx)), (1, 1500+10*(120-yy))])# maybe

    def _along(self, frame):
        pass
        # xx, _ = self._find_center_error(frame, MASK_POS)
        # self.output([(3, 160-xx), (1, 1600)])# maybe

    def _around(self, frame):
        pass

    def _detect(self, frame)

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
            self.output_queue.get(timeout=0.001)
        self.output_queue.put(*arg, **kws)

if __name__ == '__main__':
    plane = Plane()
    plane.arm()
    # plane.throttle_test()
    plane.take_off()
    plane.land()
    plane.disarm()