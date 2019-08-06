from functions import *
from time import time
debug = 1
STOPTIME = 60*5
"""
標準流程
ARM
起飛    快速拉高
穩定    定位在圓圈上方 盡量穩定
循線    沿線走
停止線  找到線 停在前面
等帶顏色轉變
循線    沿線走
找到色塊    
(懸停)
投放
循線
找到紅線
找到目標
穩定
降落
DISARM
"""
"""
感覺不需要I跟D (因為有光流)
"""



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

    