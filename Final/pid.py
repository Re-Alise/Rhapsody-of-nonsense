from time import sleep, time

SAMPLE_TIME = 0.01
# ITerm limit
WINDUP_GUARD = 80

class PID():
    def __init__(self, kp=1, ki=0, kd=0, debug=0, windup_guard=WINDUP_GUARD):
        self.Kp = kp
        self.Ki = ki
        self.Kd = kd
        self.output = 0
        self.current_time = time()
        self.last_time = self.current_time
        self.last_error = 0
        self.min = -50*8
        self.max = 50*8
        self.ITerm = 0
        self.windup_guard = windup_guard
        self.pid = (kp, ki, kd, windup_guard)
        self.debug = debug

    def update(self, error=None):
        # if not error:
        #     self.ITerm = 0
        #     self.last_error = 0
        #     return 0
        self.current_time = time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        # min working interval
        if (delta_time >= SAMPLE_TIME):
            PTerm = self.Kp * error
            self.ITerm += self.Ki * error * delta_time
            if error * self.last_error < 0 or (abs(self.last_error) > abs(error) and abs(error) < 30):
                if error != 0:
                    self.ITerm = 0
            
            # Iterm limit
            if (self.ITerm < -self.windup_guard):
                self.ITerm = -self.windup_guard
            elif (self.ITerm > self.windup_guard):
                self.ITerm = self.windup_guard

            if delta_time > 0:
                DTerm = self.Kd * delta_error / delta_time
            else:
                DTerm = 0.0

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            self.output = int(PTerm + self.ITerm + DTerm)
            if self.debug:
                print('PID values:', error, PTerm, self.ITerm, (self.Kd * DTerm), self.output)
        return self.output

    def setkp(self, n):
        self.Kp = n
    def setki(self, n):
        self.Ki = n
    def setkd(self, n):
        self.Kd = n
    def set_windup_guard(self, windup_guard):
        self.windup_guard = windup_guard

    def reset(self):
        self.ITerm = 0
        self.Kp, self.Ki, self.Kd, self.windup_guard = self.pid

    def set_pid(self, kp=1, ki=0, kd=0):
        self.ITerm = 0
        self.Kp = kp
        self.Ki = ki
        self.Kd = kd
