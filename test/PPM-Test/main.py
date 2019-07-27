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

    def __init__(self, input_queue, gpio, channel=8, frame_ms=20):
        Thread.__init__(self)
        self._input_queue = input_queue
        self._gpio = gpio
        self._channel = channel
        self._pi = pigpio.pi()

        if not self._pi.connected:
            print('Error: pigpio is not initialized')
            exit(0)

        self._pi.wave_tx_stop()  # Start with a clean slate.
        self._ppm = PPM(self._pi, self._gpio, channel=channel, frame_ms=frame_ms)
        # Default output signal for stablizing
        self._ppm.update_channels([1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500])

    def run(self):
        while 1:
            if not self._input_queue.empty():
                signals = self._input_queue.get()
                if not isinstance(signals, list):
                    continue

                if len(signals) != self._channel:
                    # input length and number of channels not matched
                    continue
                
                self._ppm.update_channels(signals)
            else:
                sleep(0.01)


if __name__ == "__main__":
    q = Queue()
    controller = PPMController(q, 6)
    signals = [1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500]
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

            if width > 7 or width < 0:
                print('Error: Index of channel out of range')
                continue

            if width > 2000 or width < 0:
                print('Error: Signal width out of range')
                continue

            signals[channel] = width
            q.put(signals)
            
    except KeyboardInterrupt:
        print("Test ended")
        GPIO.cleanup()
