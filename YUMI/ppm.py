import time
import pigpio


class PPM:
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

    def __init__(self, pi, gpio, channels=8, frame_ms=20):
        self.adjust = 1
        self.pi = pi
        self.gpio = gpio

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

        pi.write(gpio, pigpio.LOW)

        self._update_time = time.time()

    def _update(self):
        wf = []
        micros = 0
        for i in self._widths:
            wf.append(pigpio.pulse(0, 1 << self.gpio, self.GAP))
            wf.append(pigpio.pulse(1 << self.gpio, 0, i))
            micros += (i+self.GAP)
        # off for the remaining frame period
        wf.append(pigpio.pulse(0, 1 << self.gpio, self.GAP))
        micros += self.GAP
        wf.append(pigpio.pulse(1 << self.gpio, 0, self._frame_us-micros))

        self.pi.wave_add_generic(wf)
        wid = self.pi.wave_create()
        self.pi.wave_send_using_mode(wid, pigpio.WAVE_MODE_REPEAT_SYNC)
        self._wid[self._next_wid] = wid

        self._next_wid += 1
        if self._next_wid >= self.WAVES:
            self._next_wid = 0

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
            self._widths[signal[0]] = signal[1]-self.GAP+1500
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