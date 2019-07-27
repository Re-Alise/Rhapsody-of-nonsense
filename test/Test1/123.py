#encoding=UTF-8
from threading import Thread
from queue import Queue
from time import sleep, time
import RPi.GPIO as GPIO
class Driver(Thread):
    def __init__(self, data):
        Thread.__init__(self)
        # RPi.GPIO.setmode(GPIO.BCM)
        ms2dutyCycle = 5
        self.data = data
        self.now = 0
        self.timeout = 0.2
        self.pinName = ('t', 'y', 'p', 'r', 's')
        self.pins = dict(zip(self.pinName, (29, 31, 33, 35, 37)))
        print(list(self.pins.values()))
        self.offset = dict(zip(self.pinName, (15, 15, 15, 15, 15)))
        self.d = self.offset
        self.cent = 0.05
        # self.cent = 0.5*ms2dutyCycle/100
        self.init()
    
    def init(self):
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(list(self.pins.values()), GPIO.OUT)
        self.throttle = GPIO.PWM(self.pins['t'], 100)
        self.yaw = GPIO.PWM(self.pins['y'], 100)
        self.pitch = GPIO.PWM(self.pins['p'], 100)
        self.row = GPIO.PWM(self.pins['r'], 100)
        self.servo = GPIO.PWM(self.pins['s'], 100)
        self.throttle.start(0)
        self.yaw.start(0)
        self.pitch.start(0)
        self.row.start(0)
        self.servo.start(0)
        

    def run(self):
        print('driver running---')
        while 1:
            if not self.data.empty():
                (key, value) = self.data.get()
                self.write(key, value)
                self.now = time()
            elif time()-self.now > self.timeout:
                # stop
                pass
            self.output()
            sleep(0.01)

    def output(self, unstop=1):
        # if unstop:
        self.throttle.ChangeDutyCycle(self.d['t'])
        self.yaw.ChangeDutyCycle(self.d['y'])
        self.pitch.ChangeDutyCycle(self.d['p'])
        self.row.ChangeDutyCycle(self.d['r'])
        self.servo.ChangeDutyCycle(self.d['s'])
        print(self.d['s'])
        # else:
        #     self.throttle.ChangeDutyCycle(self.offset['t'])
        #     self.yaw.ChangeDutyCycle(self.offect['y'])
        #     self.pitch.ChangeDutyCycle(self.offect['p'])
        #     self.row.ChangeDutyCycle(self.offect['r'])
        #     self.servo.ChangeDutyCycle(self.offect['s'])

    def write(self, key=None, value=0):
        if key:
            self.d[key] = value*self.cent+self.offset[key]
        else:
            self.d = dict.fromkeys(self.pinName, value)


if __name__ == '__main__':
    q = Queue()
    driver = Driver(q)
    driver.daemon = 1
    driver.start()
    q.put(('t', 0))
    q.put(('y', 0))
    q.put(('p', 0))
    q.put(('r', 0))
    q.put(('s', 0))
    input('')