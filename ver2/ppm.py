from threading import Thread
import time
import ins
try:
    import pigpio
except ImportError:
    import mpigpio as pigpio

# @ins.only
# class Controller(Thread):
#     """PPM output controller powered by pigpio

#     **Start the pigpio daemon before running: sudo pigpiod**

#     Arguments:
#     input_queue -- Queue to trans
#     gpio -- Number of output pin, equivalent to GPIO.BCM (GPIOX)
#     channel -- Number of PPM channel (8 default)
#     frame_ms -- Time interval between frames in microsecond (5 minimum, 20 default)

#     Source: https://www.raspberrypi.org/forums/viewtopic.php?t=219531
#     """

#     def __init__(self, input_queue, gpio, channels=8, frame_ms=20, gpio_sonic=19):
#         Thread.__init__(self)
#         self._input_queue = input_queue
#         self._gpio = gpio
#         self._channels = channels
#         self._pi = ins.get_only(pigpio.pi)

#         if not self._pi.connected:
#             print('Error: pigpio is not initialized')
#             exit(0)

#         self._ppm = PPM(self._pi, self._gpio, channels=channels, frame_ms=frame_ms, gpio_sonic=gpio_sonic)
#         # Default output signal for stablizing
#         self._ppm.update_channels([1500, 1500, 1100, 1500, 1500, 1500, 1500, 1500])
#         self.daemon = 1
#         self.start()

#     def run(self):
#         while 1:
#             signals = self._input_queue.get()
#             self._ppm.update_assign(signals)
@ins.only
class PPM(Thread):
    """8 channel PPM output powered by pigpio

    **Start the pigpio daemon before running: sudo pigpiod**

    Arguments:
    pi -- pigpio.pi()
    gpio -- Number of output pin, equivalent to GPIO.BCM (GPIOX)
    channel -- Number of PPM channel (8 default)
    frame_ms -- Time interval between frames in microsecond (5 minimum, 20 default)

    Source: https://www.raspberrypi.org/forums/viewtopic.php?t=219531
    """
    GAP = 400
    WAVES = 3

    def __init__(self, input_queue, gpio, channels=8, frame_ms=20, gpio_sonic=19):
        Thread.__init__(self)
        self.adjust = 1
        self._input_queue = input_queue
        self.pi = ins.get_only(pigpio.pi)
        self.gpio = gpio
        self.gpio_sonic = gpio_sonic

        if frame_ms < 5:
            frame_ms = 5
            channels = 2
        elif frame_ms > 100:
            frame_ms = 100

        self.frame_ms = frame_ms

        self._frame_us = int(frame_ms * 1000)
        self._frame_secs = frame_ms / 1000.0

        if channels < 1:
            channels = 1
        elif channels > (frame_ms // 2):
            channels = int(frame_ms // 2)

        self.channels = channels

        # set each channel to minimum pulse width
        self._widths = [1000] * channels

        self._wid = [None]*self.WAVES
        self._next_wid = 0

        self.pi.write(gpio, pigpio.LOW)
        self.pi.write(gpio_sonic, pigpio.LOW)

        self._update_time = time.time()

        self.update_channels([1500, 1500, 1100, 1500, 1500, 1500, 1500, 1500])
        self.daemon = 1
        self.start()

    def run(self):
        while 1:
            signals = self._input_queue.get()
            self.update_assign(signals)

    def _update(self):
        # 建立waveform
        wf = []
        micros = 0
        for i in self._widths:
            wf.append(pigpio.pulse(0, 1 << self.gpio, self.GAP))
            wf.append(pigpio.pulse(1 << self.gpio, 0, i))
            micros += (i+self.GAP)
        wf.append(pigpio.pulse(0, 1 << self.gpio, self.GAP-15))
        # 超音波trig也順便發出
        wf.append(pigpio.pulse(1 << self.gpio_sonic, 0, 15))
        micros += self.GAP
        wf.append(pigpio.pulse(1 << self.gpio, 1 << self.gpio_sonic, self._frame_us-micros))

        # 建立wf並傳送出去（嘗試同步）
        self.pi.wave_add_generic(wf)
        wid = self.pi.wave_create()
        self.pi.wave_send_using_mode(wid, pigpio.WAVE_MODE_REPEAT_SYNC)
        self._wid[self._next_wid] = wid

        self._next_wid += 1
        if self._next_wid >= self.WAVES:
            self._next_wid = 0

        # 等發送完一次之後才能繼續
        remaining = self._update_time + self._frame_secs - time.time()
        if remaining > 0:
            time.sleep(remaining)
        self._update_time = time.time()

        wid = self._wid[self._next_wid]
        if wid is not None:
            self.pi.wave_delete(wid)
            self._wid[self._next_wid] = None

    def update_assign(self, signals):
        for signal in signals:
            self._widths[signal[0]] = signal[1]*8-self.GAP+1500
        self._update()

    def update_channel(self, channel, width):
        # self._widths[channel] = width
        self._widths[channel] = width - self.GAP # workaround for singal offset problem
        self._update()

    def update_channels(self, widths):
        # self._widths[0:len(widths)] = widths[0:self.channels]
        self._widths[0:len(widths)] = [w - self.GAP for w in widths[0:self.channels]] # workaround for singal offset problem
        self._update()

    def cancel(self):
        self.pi.wave_tx_stop()
        for i in self._wid:
            if i is not None:
                self.pi.wave_delete(i)


if __name__ == "__main__":
    # pi = pigpio.pi()
    # pi.write(6, 1)
    # input('>>>')

    # if not pi.connected:
    #     exit(0)

    # pi.wave_tx_stop()  # Start with a clean slate.

    # ppm = PPM(pi, 6, frame_ms=20)

    # # updates = 0
    # # start = time.time()
    # # for chan in range(8):
    # #     for pw in range(1000, 2000, 5):
    # #         ppm.update_channel(chan, pw)
    # #         updates += 1
    # # end = time.time()
    # # secs = end - start
    # # print("{} updates in {:.1f} seconds ({}/s)".format(updates, secs, int(updates/secs)))
    # # time.sleep(2)
    # input()

    # ppm.cancel()

    # pi.stop()
    pass