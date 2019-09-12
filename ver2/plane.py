import ins

def verbose(f):
    def _f(*args, **kwargs):
        print('{:^50}'.format(f.__name__).replace(' ', '-'))
        f(*args, **kwargs)
        print('-'*50)
    return _f

def p(*arg, **kws):

    if DEBUG:
        print(*arg, **kws)

class Plane():
    """main program
    """

    def __init__(self):
        # just one buffer because we just need the last value
        self.output_count = 0
        self.output_queue = Queue(1)
        # self.cap = cv2.VideoCaptures(0)
        self._pi = ins.get_only(pigpio.pi)
        self._pi.wave_tx_stop()
        self.sonic = Sonic(self._pi)
        self.lidar = TFMiniLidar(TF_PORT, debug=DEBUG)
        self.hight = 130
        Controller(self.output_queue, 13)
        self.pitch = 0
        self.yaw = 0
        self.row = 0
        self.colors = (0, 0, 0, 0)
        # self.capture = cv2.VideoCapture(2)

    @verbose
    def arm(self):
        self.reset()
        sleep(0.1)
        self.output([(DC.THROTTLE, -50), (DC.YAW, 50)]) # set throttle to lowest, yaw to right
        sleep(2)
        self.output([(DC.THROTTLE, 0)])
        sleep(1)

    @verbose
    def reset(self):
        self.output_count = 0
        
    @verbose
    def mc(self, mode):
        if mode == DC.OpticsFlow:
            self.output([(DC.MODE, -50)])
        else:
            self.output([(DC.MODE, 50)])
        # 保證切換完畢
        sleep(0.04)

    @verbose
    def take_off(self, hight, speed=10):
        """依靠超音波 去起飛
        """
        self.output([(DC.PITCH, 0), (DC.ROLL, 0), (DC.THROTTLE, speed), (DC.YAW, 0)])
        while self.lidar.value < hight:
            sleep(LOOP_INTERNAL)
        self.output([(DC.THROTTLE, 0)])

    @verbose
    def throttle_test(self):
        self.output([(DC.THROTTLE, 0)])
        sleep(0.1)
        self.output([(DC.THROTTLE, -50)])

    @verbose
    def idle(self, sec=1):
        now = time()
        if sec>0:
            while time()-now<sec:
                self.check()
                self.output([(DC.PITCH, self.pitch), (DC.ROW, self.row), (DC.YAW, self.yaw)])
                sleep(LOOP_INTERNAL)

    def check(self, overhight=80):
        if self.sonic.value>overhight:
            print('Mission Fail')
            self.output([(DC.THROTTLE, -30), (DC.MODE, -50), (DC.YAW, 0), (DC.PITCH, 0), (DC.ROW, 0)])
            while 1:
                print('Mission Fail')
                sleep(0.1)


    @verbose
    def land(self):
        self.output([(DC.PITCH, 0), (DC.ROLL, 0), (DC.THROTTLE, -LAND_SPEED), (DC.YAW, 0),])
        while self.sonic.value>8:
            sleep(LOOP_INTERNAL)
        self.output([(DC.THROTTLE, -50)])
        while self.sonic.value>4:
            sleep(LOOP_INTERNAL)

    @verbose
    def disarm(self):
        self.output([(DC.THROTTLE, -50), (DC.YAW, -50)]) # set throttle to lowest, yaw to lift
        sleep(5)
        self.output([(DC.YAW, 0)])

    # def _stabilize(self, frame, color):
    #     xx, yy, _ = self._find_center(frame, MASK_ALL)
    #     pitch = 120-yy
    #     row = xx-160
    #     self.output([()])

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

    # def _find_center(self, frame, mask):
    #     frame = cv2.bitwise_and(frame, frame, mask=mask)
    #     contours, _ = cv2.findContours(frame,1,2)
    #     sumX=0
    #     sumY=0
    #     sumW=0
    #     for cnt in contours:
    #         M=cv2.moments(cnt)
    #         sumX += M['m10']
    #         sumY += M['m01']
    #         sumW += M['m00']
    #         # M['M00'] weight
    #         # M['m10'] xMoment
    #         # M['m01'] yMoment
    #     # 全畫面的黑色的中心座標
    #     if sumW == 0:
    #         print('Not found')
    #         return -1, -1, 0
    #     cX = int(sumX/sumW)
    #     cY = int(sumY/sumW)
    #     return cX, cY, sumW

    def output(self, *arg, **kws):
        self.output_count += 1
        while self.output_queue.full():
            try:
                self.output_queue.get(timeout=0.00001)
            except:
                pass
        self.output_queue.put(*arg, **kws)
