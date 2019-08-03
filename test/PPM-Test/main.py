from ppm import PPM
from threading import Thread
from queue import Queue
from time import sleep

import pigpio


class PPMController(Thread):
    """PPM output controller powered by pigpio

    **Start the pigpio daemon before running: sudo pigpiod**

    Arguments:
    input_queue -- Queue to trans
    gpio -- Number of output pin, equivalent to GPIO.BCM (GPIOX)
    channel -- Number of PPM channel (8 default)
    frame_ms -- Time interval between frames in microsecond (5 minimum, 20 default)

    Source: https://www.raspberrypi.org/forums/viewtopic.php?t=219531
    """

    def __init__(self, input_queue, gpio, channels=8, frame_ms=20):
        Thread.__init__(self)
        self._input_queue = input_queue
        self._gpio = gpio
        self._channels = channels
        self._pi = pigpio.pi()

        if not self._pi.connected:
            print('Error: pigpio is not initialized')
            exit(0)

        self._pi.wave_tx_stop()  # Start with a clean slate.
        self._ppm = PPM(self._pi, self._gpio, channels=channels, frame_ms=frame_ms)
        # Default output signal for stablizing
        self._ppm.update_channels([1500, 1500, 1100, 1500, 1500, 1500, 1500, 1500])
        self.daemon = 1
        self.start()

    def run(self):
        while 1:
            if not self._input_queue.empty():
                signals = self._input_queue.get()
                if not isinstance(signals, list):
                    continue

                if len(signals) != self._channels:
                    # input length and number of channels not matched
                    continue
                
                self._ppm.update_channels(signals)
            else:
                sleep(0.01)


def arm(q:Queue, signal:list):
    # signal[3] = 1500
    sleep(0.1)
    signal[2] = 1100 # set throttle to lowest
    signal[3] = 1900 # set yaw to right
    q.put(signal)
    sleep(2)
    signal[3] = 1500 # set yaw to center
    q.put(signal)


def disarm(q:Queue, signal:list):
    signal[2] = 1100  # set throttle to lowest
    signal[3] = 1100  # set yaw to left
    q.put(signal)
    sleep(5)
    signal[3] = 1500  # set yaw to center
    q.put(signal)

def throttle_test(q:Queue, signal:list):
    signal[2] = 1500  # set throttle to 1500
    q.put(signal)
    sleep(0.1)
    signal[2] = 1100  # set throttle to 1100
    q.put(signal)

def test():
    try:
        while 1:
            channel = input('Channel: ')
            width = input('Signal width(us): ')
            try:
                channel = int(channel)
                width = int(width)
            except:
                print('Error: invalid channel or width format')
                continue

            if channel > 7 or channel < 0:
                print('Error: Index of channel out of range')
                continue

            if width > 2000 or width < 0:
                print('Error: Signal width out of range')
                continue

            signals[channel] = width
            q.put(signals)
            
    except KeyboardInterrupt:
        print("Test ended")


if __name__ == "__main__":
    q = Queue()
    controller = PPMController(q, 6, channels=8)
    signals = [1500, 1500, 1100, 1500, 1500, 1500, 1500, 1500]
    print('arm')
    arm(q, signals)
    print('arm end')
    input()
    print('warnging!!!')
    throttle_test(q, signals)
    print('disarm')
    disarm(q, signals)
    print('disarm end')
    print('test ended')
    input()
# 1478,	1479,	1093,	1477,	1086,	1086,	1479,	1477,   normal
# 1457,	1465,	1071,	1856,	1078,	1078,	1465,	1463,	arm
# 1471,	1471,	1078,	1071,	1070,	1070,	1471,	1461,   disarm
