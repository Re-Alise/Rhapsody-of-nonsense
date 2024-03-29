from time import sleep
from data import PIN
from plane import verbose
from tool import *

try:
    import pigpio
except ImportError:
    print('Warning: pigio is NOT imported')
    import mpigpio as pigpio

@only
class Box():
    def __init__(self):
        self.pi = get_only(pigpio.pi)

    @verbose
    def drop(self, width=1700):
        self.pi.set_servo_pulsewidth(PIN.BOX, width)

    @verbose
    def close(self, width=870):
        self.pi.set_servo_pulsewidth(PIN.BOX, width)


from threading import Thread
class TBox(Thread):
    def __init__(self):
        super(TBox, self).__init__()
        self.pi = get_only(pigpio.pi)
        self.daemon = 1
        self.start()

    
    @verbose
    def drop(self):
        self.pi.set_servo_pulsewidth(PIN.BOX, 1700)

    @verbose
    def close(self):
        self.pi.set_servo_pulsewidth(PIN.BOX, 870)

    def run(self):
        while True:
            self.drop()
            sleep(1)
            self.close()
            sleep(1)


if __name__ == "__main__":
    box = Box()
    box.drop()
    sleep(1)
    box.close()
    print('Test finished')