from queue import Queue

from serialport import serial_ports
from sonic import Sonic
from tfmini import TFMiniLidar
from ppm import Controller
from data import DC, STATE
from time import sleep, time

import pigpio
import ins

DEBUG = False

TAKEOFF_SPEED   = 22
LAND_SPEED      = 18
NORMAL_SPEED    = 10
LOOP_INTERNAL   = 0.0005

ports = serial_ports('ttyUSB')
if len(ports) == 0:
    print('No serial connection detected')
    exit()
TF_PORT = ports[0]

def verbose(f):
    def _f(*args, **kwargs):
        print('{:^50}'.format(f.__name__).replace(' ', '-'))
        f(*args, **kwargs)
        print('-'*50)
    return _f

def p(*arg, **kws):

    if DEBUG:
        print(*arg, **kws)

@ins.only
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
        self.sonic = Sonic()
        self.lidar = TFMiniLidar(TF_PORT, debug=DEBUG)
        self.hight = 130
        Controller(self.output_queue, 13)
        # -------------------------
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
                self.output([(DC.PITCH, self.pitch), (DC.ROLL, self.row), (DC.YAW, self.yaw)])
                sleep(LOOP_INTERNAL)

    def check(self, overhight=80):
        if self.sonic.value>overhight:
            self.fail('plane.Plane.check', 'over hight: '+str(overhight))

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

    def output(self, *arg, **kws):
        self.output_count += 1
        while self.output_queue.full():
            try:
                self.output_queue.get(timeout=0.00001)
            except:
                pass
        self.output_queue.put(*arg, **kws)

    def update(self, noERROR,  pitch, roll, yaw):
        if noERROR:
            self.output([(DC.YAW, yaw), (DC.PITCH, pitch), (DC.ROLL, roll)])
        else:
            self.fail('plane.Plane.update', 'recive error flag')

    def fail(self, souce='unknow', msg=''):
        print('Mission Fail')
        self.output([(DC.THROTTLE, -30), (DC.MODE, -50), (DC.YAW, 0), (DC.PITCH, 0), (DC.ROLL, 0)])
        while 1:
            print(souce, 'get ERROR!')
            print('Mission Fail!', msg)
            sleep(0.5)