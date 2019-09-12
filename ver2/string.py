from enum import IntEnum, auto

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

if __name__ == '__main__':
    print("It isn't a program")