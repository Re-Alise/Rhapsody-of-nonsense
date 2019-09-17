from threading import Thread
from serial import Serial
from serial.serialutil import SerialException, SerialTimeoutException
from time import sleep
from serialport import serial_ports
import ins

TF_BAUDRATE = 115200
DIST_L = 2
DIST_H = 3
STRENGTH_L = 4
STRENTGTH_H = 5

DEBUG = False

def measure(s: Serial, loop=False):
    count = 0
    data = []
    while 1:
        try:
            b = s.read()
        except SerialException:
            raise SerialException
        else:
            if b == b'Y':
                if count == 0 or count == 1:
                    # Start reading data
                    count += 1
                    data.append(b)
                elif count > 9:
                    # Data is corrupted, reset everything
                    if DEBUG:
                        print('Data corrupted (too long), reset')
                    count = 1
                    data = [b]
                elif count == 9:
                    # Data is complete, varify checksum
                    if DEBUG:
                        print('TF raw data:', data)

                    if len(data) != 9:
                        # Data is corrupted, reset everything
                        if DEBUG:
                            print('Data corrupted, reset')
                        count = 1
                        data = [b]
                        continue
                    checksum = int.from_bytes(data[8], byteorder='little')
                    datasum = sum([int.from_bytes(i, byteorder='little')
                                for i in data[:8]]) % 256

                    if DEBUG:
                        print('Data sum:', datasum, '\tChecksum:', checksum)

                    if checksum == datasum:
                        dist = int.from_bytes(
                            data[DIST_L] + data[DIST_H], byteorder='little')
                        if DEBUG:
                            print('Distance:', dist, 'cm')

                        if not loop:
                            return dist

                    count = 1
                    data = [b]

            else:
                if count == 0 or count == 1:
                    # Data is imcomplete one, reset and skip to next frame
                    data.clear()
                    continue

                data.append(b)
                count += 1

@ins.only
class TFMiniLidar(Thread):
    read = False
    port = None
    value = 0

    def __init__(self, port: str=None, debug=False):
        Thread.__init__(self)
        if not self.port:
            print('TF mini lidar error: No port information')
            raise IOError

        try:
            self.s = Serial(self.port, TF_BAUDRATE, timeout=0.1)
        except:
            print('TF mini lidar error: Port could not open')
            raise IOError

        self.debug = debug
        self.daemon = 1
        self.value = 0
        if port:
            self.port = port
        else:
            print('no port')
        self.start()

    def run(self):
        while 1:
            try:
                dist = measure(self.s)
            except SerialException:
                print('Something bad with serial connection, reconnecting...')
                self.s = Serial(self.port, TF_BAUDRATE, timeout=0.1)
                continue

            if self.debug:
                # print('lidar distance:' ,dist)
                pass
            self.value = dist
            sleep(0.01)


if __name__ == '__main__':
    ports = serial_ports('ttyUSB')
    if len(ports) == 0:
        print('No serial connection detected')
        exit()
    s = Serial(ports[0], TF_BAUDRATE, timeout=0.1)
    measure(s, loop=True)
