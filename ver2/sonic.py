from time import time, sleep
import ins
try:
    import pigpio
except ImportError:
    print('Warning: pigio is NOT imported')

@ins.only
class Sonic():
    def __init__(self, trigger_pin=19, echo_pin=26):
        print('sonic init')
        self._pi = ins.get_only(pigpio.pi)
        self._pi.callback(echo_pin, pigpio.EITHER_EDGE, self.dealt)
        self.value = 0
        self.time_rise = 0

    # 怕因為溢位而出問題
    def dealt(self, gpio, level, tick):
        if level == 1: # rising
            self.time_rise = tick
            # self.num1+=1
        elif level == 0: # falling
        # if self.num
            passTime = tick-self.time_rise
            if passTime < 25000:
                self.value = passTime*.017150

if __name__ == '__main__':
    # sonic = Sonic(pigpio.pi())
    # now = time()
    # times = 0
    # while time()-now < 10:
    #     times+=1
    #     sleep(.1)
    #     print('value:', self.value)
    # print(times)
    input('test finish')
        
