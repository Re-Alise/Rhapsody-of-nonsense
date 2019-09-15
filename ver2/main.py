from time import time, sleep
from threading import Thread
from queue import Queue
from plane import Plane
from sonic import Sonic
from tfmini import TFMiniLidar
from data import PIN, DC, MASK
from camera import Record
from controller import Controller

import os
import ins
import cv2
try:
    import pigpio
except ImportError:
    print('Warning: pigio is NOT imported')


BUZZER_INTERVAL_L = 0.5
BUZZER_INTERVAL_H = 1 - BUZZER_INTERVAL_L

buzzer_time = time()
buzzer_state = 0

def beep(pi):
    global buzzer_time, buzzer_state
    # print(buzzer_time)
    delta = abs(time() - buzzer_time)
    if buzzer_state == 0:
        interval = BUZZER_INTERVAL_L
    else:
        interval = BUZZER_INTERVAL_H 
    if delta > interval:
        # global buzzer_time
        buzzer_state = abs(buzzer_state - 1)
        pi.write(PIN.BUZZER, buzzer_state)
        buzzer_time = time()

if __name__ == '__main__':
    gpio = ins.get_only(pigpio.pi)
    gpio.set_mode(PIN.BUZZER, pigpio.OUTPUT)
    plane = Plane()
    controller = Controller()
    mode_auto = gpio.read(PIN.STATE)                                   
    print('init finish-------------------------------')
    while 1:
        try:
            start_signal = gpio.read(PIN.STATE)
            if start_signal and not mode_auto:
                gpio.write(PIN.BUZZER, 0)
                mode_auto = 1
                # auto run
                print('mission start')
                controller.record.start()
                plane.arm()
                plane.mc(DC.OpticsFlow)
                plane.take_off(70, 22)
                plane.take_off(120, 10)
                plane.idle(5)
                controller.mission_start()

                plane.land()
                plane.mc(DC.Manual)
                plane.disarm()
                controller.stop()
                print('mission completed')
            else:
                if not start_signal:
                    mode_auto = 0
            # print(start_signal)
            beep(gpio)
            sleep(.1)
        except KeyboardInterrupt:
            print('owo')
            gpio.write(PIN.BUZZER, 0)
            break

