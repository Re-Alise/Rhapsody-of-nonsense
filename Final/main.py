from time import time, sleep
from threading import Thread
from queue import Queue
from plane import Plane
from sonic import Sonic
from box import Box, TBox
from tfmini import TFMiniLidar
from data import PIN, DC, MASK
from camera import Record
from controller import Controller

import os
import tool
import cv2
import sys

try:
    import pigpio
except ImportError:
    print('Warning: pigio is NOT imported')
    import mpigpio as pigpio


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
    print('===============Ver3================')
    yolo = 0
    if len(sys.argv)>1:
        if sys.argv[1] == 'n':
            save = 0
        else:
            save = 1

        if sys.argv[1] == '1':
            yolo = 1
            print('Warning: YOLO strategy 1')

        if sys.argv[1] == '2':
            yolo = 2
            print('Warning: YOLO strategy 2')

        if sys.argv[1] == '3':
            yolo = 3
            print('Warning: YOLO strategy 3')
    else:
        save = 1

    try:
        box = Box()
        gpio = tool.get_only(pigpio.pi)
        gpio.set_mode(PIN.BUZZER, pigpio.OUTPUT)
        plane = Plane()
        controller = Controller(debug=False, save=save)
        mode_auto = gpio.read(PIN.STATE)
    except:
        print('!!!init fail')      
        exit()                       
    box.close()
    print('init finish-------------------------------')
    # box.drop()
    # sleep(1)
    while 1:
        try:
            start_signal = gpio.read(PIN.STATE)
            if start_signal and not mode_auto:
                gpio.write(PIN.BUZZER, 0)
                mode_auto = 1
                # auto run
                print('mission start')
                controller.record.start()
                plane.mc(DC.LOITER)
                plane.arm()
                plane.take_off(55, 16*8)
                # plane.take_off(100, 10*8)
                plane.take_off(90, 10*8)
                plane.idle(5)
                if yolo == 1:
                    controller.mission_yolo_1()
                elif yolo == 2:
                    controller.mission_yolo_2()
                elif yolo == 3:
                    controller.mission_yolo_3()
                else:
                    controller.mission_start()

                box.close()
                plane.land()
                plane.mc(DC.STABLIZE)
                plane.disarm()
                controller.stop()
                print('mission completed')
                break
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

