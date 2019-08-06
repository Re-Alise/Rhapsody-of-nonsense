from queue import Queue
from threading import Thread

# maybe contraller for the plane
class Plane(Thread):
    def __init__(self, input_queue:Queue):
        Thread.__init__(self)
        self.daemon = 1
        self._input_queue = input_queue