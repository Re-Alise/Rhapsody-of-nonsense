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
    def drop(self, width=1500):
        self.pi.set_servo_pulsewidth(PIN.BOX, width)

    @verbose
    def close(self, width=900):
        self.pi.set_servo_pulsewidth(PIN.BOX, width)


if __name__ == "__main__":
    box = Box()
    box.drop()
    sleep(1)
    box.close()
    print('Test finished')