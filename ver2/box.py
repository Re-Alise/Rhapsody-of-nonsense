from time import sleep
from data import PIN
from plane import verbose
# from tool import *
import ins


try:
    import pigpio
except ImportError:
    print('Warning: pigio is NOT imported')
    import mpigpio as pigpio

@ins.only
class Box():
    def __init__(self):
        self.pi = ins.get_only(pigpio.pi)

    @verbose
    def drop(self):
        self.pi.set_servo_pulsewidth(PIN.BOX, 1800)

    @verbose
    def close(self):
        self.pi.set_servo_pulsewidth(PIN.BOX, 1036)


from threading import Thread
class TBox(Thread):
    def __init__(self):
        super(TBox, self).__init__()
        self.pi = ins.get_only(pigpio.pi)
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