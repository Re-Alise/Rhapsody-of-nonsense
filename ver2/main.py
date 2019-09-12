from time import time, sleep
from threading import Thread
from queue import Queue
from plane import Plane
from ppm import Controller
from sonic import Sonic
from tfmini import TFMiniLidar
import pigpio
import os
import ins

PIN_BUZZER = 11
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
        pi.write(PIN_BUZZER, buzzer_state)
        buzzer_time = time()



if __name__ == '__main__':
    gpio = ins.get_only(pigpio.pi)
    gpio.set_mode(PIN_BUZZER, pigpio.OUTPUT)
    plane = Plane()
    # plane.sonic.test(100)
    mode_auto = pp.read(6)                          
                                                                         
    print('init finish-------------------------------')
    while 1:
        try:
            start_signal = gpio.read(6)
            if start_signal and not mode_auto:
                # main program
                pass
            else:
                if not start_signal:
                    mode_auto = 0
            # print(start_signal)
            beep(gpio)
            sleep(.1)
        except KeyboardInterrupt:
            print('owo')
            gpio.write(PIN_BUZZER, 0)
            break

