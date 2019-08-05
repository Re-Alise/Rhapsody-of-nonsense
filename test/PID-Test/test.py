from threading import Thread
from queue import Queue
from time import sleep
import time

class PID(Thread):
    def __init__(self, input_queue:Queue, kp=1, ki=0, kd=0, sample_time=0.01):
        Thread.__init__(self)
        self.daemon = 1
        self._input_queue = input_queue
        self.set_point = 0
        self.Kp = kp
        self.Ki = ki
        self.Kd = kd
        self.output = 0
        self.sample_time = sample_time
        self.current_time = time.time()
        self.last_time = self.current_time
        self.last_error = 0
        self.min = 0
        self.max = 100
        self.ITerm = 0
    
    def run(self):
        while 1:
            if not self._input_queue.empty():
                self._update(self._input_queue.get())
            else:
                sleep(0.01)

    def _update(self, feedback_value):
        error = self.set_point - feedback_value
        self.current_time = time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        # min working interval
        if (delta_time >= self.sample_time):
            self.PTerm = self.Kp * error
            self.ITerm += error * delta_time
            
            # Iterm limit
            # if (self.ITerm < -self.windup_guard):
            #     self.ITerm = -self.windup_guard
            # elif (self.ITerm > self.windup_guard):
            #     self.ITerm = self.windup_guard

            if delta_time > 0:
                self.DTerm = delta_error / delta_time
            else:
                self.DTerm = 0.0

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            self.output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

    def setvalue(self, n):
        self.setpoint = n
    def setkp(self, n):
        self.kp = n
    def setki(self, n):
        self.ki = n
    def setkd(self, n):
        self.kd = n