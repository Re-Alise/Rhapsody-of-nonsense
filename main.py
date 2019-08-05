from functions import *
from time import time
debug = 1
STOPTIME = 60*5

test = [
    (printTest, 123, {}),
]

if __name__ == '__main__':
    # open threads to contral plane

    # deside action from mission list
    mission = test
    for task in mission:
        f, *arg, kwargs = task
        if debug:
            print('#', f.__name__, 'start')
        f(*arg, **kwargs)
        if debug:
            print('#', f.__name__, 'finish')

    