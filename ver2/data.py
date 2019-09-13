from enum import IntEnum, auto
import numpy as np

class DC(IntEnum):
    PITCH = 0
    ROLL = 1
    THROTTLE = 2
    YAW = 3
    MODE = 4 # -50 auto, 50 manual
    AUTO = 5
    OpticsFlow = auto()
    Manual = auto()

class STATE(IntEnum):
    STABLE_K = auto()
    STABLE_R = auto()

class PIN(IntEnum):
    SNOIC_TRIG = 19
    SNOIC_ECHO = 26
    OUTPUT = 13
    BUZZER = 11
    STATE = 6

class COLOR(IntEnum):
    K = 3
    R = 2
    G = 1
    B = 0

class MASK():
    ORIGIN = np.zeros([240, 320],dtype=np.uint8)
    
    ALL = ORIGIN
    FORWARD = ORIGIN
    TOP = ORIGIN
    BUTTON = ORIGIN
    LINE_MIDDLE = ORIGIN
    RIGHT = ORIGIN

    ALL[0:240, 40:280] = 255
    FORWARD[10:90, 10:310] = 255
    TOP[0:120, 0:320] = 255
    BUTTON[121:240, 0:320] = 255
    LINE_MIDDLE[101:140, 81:240] = 255
    RIGHT[106:320, 0:240] = 255

if __name__ == '__main__':
    print("It isn't a program")