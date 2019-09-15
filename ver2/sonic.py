from time import time, sleep
import pigpio
import ins

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
    gpio = pigpio.pi()
    gpio.write(gpio_sonic, pigpio.LOW)
    
    # 建立waveform
    wf = []
    micros = 0
    wf.append(pigpio.pulse(1 << self.gpio_sonic, 0, 15))
    wf.append(pigpio.pulse(1 << self.gpio, 1 << self.gpio_sonic, 20000-15))

    # 建立wf並傳送出去（嘗試同步）
    gpio.wave_add_generic(wf)
    wid = self.pi.wave_create()
    gpio.wave_send_using_mode(wid, pigpio.WAVE_MODE_REPEAT_SYNC)

    

    sonic = Sonic(gpio)
    now = time()
    times = 0
    while time()-now < 10:
        times+=1
        sleep(.1)
        print('value:', self.value)

    print(times)
    print('test finish')
    gpio.wave_tx_stop()
    gpio.wave_delete(wid)
        
