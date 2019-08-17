from threading import Thread
from time import time, sleep

class A():
    def __init__(self):
        self.a = 0
    def set5(self):
        self.a = 5

class B(Thread):
    def __init__(self, a):
        Thread.__init__(self)
        self.daemon = 1
        self.a = a
        self.start()

    def run(self):
        self.a.set5()

if __name__ == "__main__":
    aa = A()
    print(aa.a)
    bb = B(aa)
    bb.join()
    print(aa.a)
