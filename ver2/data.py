from enum import IntEnum, auto
import numpy as np
import ins

class DC(IntEnum):
    PITCH = 1
    ROLL = 0
    THROTTLE = 2
    YAW = 3
    MODE = 4 # -50 auto, 50 manual
    AUTO = 5

    # Flight modes
    LOITER = auto()
    ALT_HOLD = auto()
    STABLIZE = auto()

class STATE(IntEnum):
    STABLE_K = auto()
    STABLE_R = auto()

class PIN(IntEnum):
    SNOIC_TRIG = 19
    SNOIC_ECHO = 26
    OUTPUT = 13
    BUZZER = 11
    STATE = 6
    BOX = 5

class COLOR(IntEnum):
    K = 3
    R = 2
    G = 1
    B = 0

@ins.only
class MASK():
    def __init__(self):
        ORIGIN = np.zeros([240, 320],dtype=np.uint8)
        
        self.ALL = ORIGIN
        self.FORWARD = ORIGIN
        self.TOP = ORIGIN
        self.BUTTON = ORIGIN
        self.LINE_MIDDLE = ORIGIN
        self.RIGHT = ORIGIN

        self.ALL[0:240, 40:280] = 255
        self.FORWARD[10:90, 10:310] = 255
        self.TOP[0:120, 0:320] = 255
        self.BUTTON[121:240, 0:320] = 255
        self.LINE_MIDDLE[101:140, 81:240] = 255
        self.RIGHT[106:320, 0:240] = 255

if __name__ == '__main__':
    print("It isn't a program")