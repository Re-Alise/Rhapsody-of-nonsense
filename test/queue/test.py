from queue import Queue
from threading import Thread
from time import time, sleep


class A(Thread):
    def __init__(self, input_queue):
        Thread.__init__(self)
        self._input_queue = input_queue
        self.daemon = 1
        self.start()

    def run(self):
        while 1:
            signals = self._input_queue.get()
            print(signals)

if __name__ == '__main__':
    now = time()
    q = Queue(1)
    A(q)
    i=1
    while time()-now<1:
        sleep(0.0001) # 可有可無 限制傳送頻率
        while q.full():
            try:
                q.get(timeout=0.00001)
            except:
                pass
        q.put(i)
        i+=1


