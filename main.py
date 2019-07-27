from fun import *
from time import time

STOPTIME = 60*5

tasks = [

]

def dealTask(task, index=0):
    startTime = time()
    while time()-startTime < STOPTIME:
        f, *arg = task[index]
        print(f, *arg)
        f(*arg)
        print('~~~~~~StepEnd~~~~~~')
        index += 1
        if not index < len(task):
            break
    print('task finish')

if __name__ == '__main__':
    # open threads to contral plane

    # deside action from mission list
    dealTask(tasks)