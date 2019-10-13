from queue import Queue

from serialport import serial_ports
from sonic import Sonic
from tfmini import TFMiniLidar
from ppm import PPM
from data import DC, STATE
from time import sleep, time
from pid import PID
from tool import *
try:
    import pigpio
except ImportError:
    display('Warning: pigio is NOT imported')
    import mpigpio as pigpio
else:
    ports = serial_ports('ttyUSB')
    if len(ports) == 0:
        display('No serial connection detected')
        exit()
    TF_PORT = ports[0]

TAKEOFF_SPEED   = 22*8
LAND_SPEED      = 18*8
NORMAL_SPEED    = 10*8
LOOP_INTERNAL   = 0.0005

def verbose(f):
    def _f(*args, **kwargs):
        display('{:^50}'.format(f.__name__).replace(' ', '-'))
        f(*args, **kwargs)
        display('-'*50)
    return _f

@only
class Plane():
    """main program
    """

    def __init__(self, debug=0):
        # just one buffer because we just need the last value
        self.output_count = 0
        self.output_queue = Queue(1)
        self.debug = debug
        # self.cap = cv2.VideoCaptures(0)
        if not debug:
            try:
                self._pi = get_only(pigpio.pi)
                self._pi.wave_tx_stop()
                self.sonic = Sonic()
                self.lidar = TFMiniLidar(TF_PORT, debug=0)
            except:
                raise IOError
        self.hight = 130
        PPM(self.output_queue, 13)
        # -------------------------
        self.yaw_pid = PID(kp=0.7)
        self.pitch_pid = PID(kp=0.35, ki=0.3, kd=0.35)
        self.roll_pid = PID(kp=0.55, ki=0.3, kd=0.25)
        # self.capture = cv2.VideoCapture(2)

    @verbose
    def arm(self):
        self.reset()
        sleep(0.1)
        self.output([(DC.THROTTLE, -400), (DC.YAW, 400)]) # set throttle to lowest, yaw to right
        sleep(2)
        self.output([(DC.THROTTLE, 0)])
        sleep(1)

    @verbose
    def reset(self):
        self.output([(DC.THROTTLE, -400), (DC.YAW, 0)])
        self.output_count = 0
        
    @verbose
    def mc(self, mode):
        if mode == DC.LOITER:
            self.output([(DC.MODE, -400)])
        elif mode == DC.ALT_HOLD:
            self.output([(DC.MODE, -100)])
        else:
            self.output([(DC.MODE, 400)])
        # 保證切換完畢
        sleep(0.04)

    @verbose
    def take_off(self, hight, speed=10*8):
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
        self.output([(DC.THROTTLE, -400)])

    @verbose
    def idle(self, sec=1):
        now = time()
        if sec>0:
            while time()-now<sec:
                # self.check()
                # self.output([(DC.PITCH, self.pitch), (DC.ROLL, self.row), (DC.YAW, self.yaw)])
                self.output([(DC.PITCH, 0), (DC.ROLL, 0), (DC.YAW, 0)])
                sleep(LOOP_INTERNAL)

    def check(self, overhight=80):
        if self.sonic.value>overhight:
            self.fail('plane.Plane.check', 'over hight: '+str(overhight))

    @verbose
    def land(self):
        self.output([(DC.PITCH, 0), (DC.ROLL, 0), (DC.THROTTLE, -LAND_SPEED), (DC.YAW, 0),])
        while self.sonic.value>8 or self.lidar.value > 35:
            sleep(LOOP_INTERNAL)
        self.output([(DC.THROTTLE, -50)])
        while self.sonic.value>4:
            sleep(LOOP_INTERNAL)

    @verbose
    def disarm(self):
        self.output([(DC.THROTTLE, -400), (DC.YAW, -400)]) # set throttle to lowest, yaw to lift
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

    def update(self, noERROR,  pitch_error, roll_error, yaw_error):
        yaw = self.yaw_pid.update(yaw_error)
        pitch = self.pitch_pid.update(pitch_error)
        roll = self.roll_pid.update(roll_error)
        display('UPDATE: yaw:', yaw, 'pitch:', pitch, 'roll:', roll)
        # Warning: Input for pitch is reversed
        if noERROR:
            self.output([(DC.YAW, yaw), (DC.PITCH, -pitch), (DC.ROLL, roll)])
        else:
            self.fail('plane.Plane.update', 'recive error flag')

    def fail(self, souce='unknow', msg=''):
        print('Mission Fail')
        self.output([(DC.THROTTLE, -30*8), (DC.MODE, -400), (DC.YAW, 0), (DC.PITCH, 0), (DC.ROLL, 0)])
        while 1:
            print(souce, 'get ERROR!')
            print('Mission Fail!', msg)
            sleep(0.5)
