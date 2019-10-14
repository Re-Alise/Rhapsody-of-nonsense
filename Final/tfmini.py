from threading import Thread
from serial import Serial
from serial.serialutil import SerialException, SerialTimeoutException
from time import sleep
from serialport import serial_ports
from tool import *

TF_BAUDRATE = 115200
DIST_L = 2
DIST_H = 3
STRENGTH_L = 4
STRENTGTH_H = 5

# except lidar fail, Don't open the DEBUG
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
                        display('Data corrupted (too long), reset')
                    count = 1
                    data = [b]
                elif count == 9:
                    # Data is complete, varify checksum
                    if DEBUG:
                        display('TF raw data:', data)

                    if len(data) != 9:
                        # Data is corrupted, reset everything
                        if DEBUG:
                            display('Data corrupted, reset')
                        count = 1
                        data = [b]
                        continue
                    checksum = int.from_bytes(data[8], byteorder='little')
                    datasum = sum([int.from_bytes(i, byteorder='little')
                                for i in data[:8]]) % 256

                    if DEBUG:
                        display('Data sum:', datasum, '\tChecksum:', checksum)

                    if checksum == datasum:
                        dist = int.from_bytes(
                            data[DIST_L] + data[DIST_H], byteorder='little')
                        if DEBUG:
                            display('Distance:', dist, 'cm')

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

@only
class TFMiniLidar(Thread):
    read = False
    port = None
    value = 0

    def __init__(self, port: str=None, debug=False):
        Thread.__init__(self)
        if not port:
            print('TF mini lidar error: No port information')
            raise IOError

        try:
            self.s = Serial(port, TF_BAUDRATE, timeout=0.1)
        except:
            print('TF mini lidar error: Port could not open')
            raise IOError

        # sanity check
        try:
            test = measure(self.s)
            print('Sanity check -- LiDAR value:', test)
        except SerialException:
            print('LiDAR (UART connection) is broken')
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
                display('Something bad with serial connection, reconnecting...')
                self.s = Serial(self.port, TF_BAUDRATE, timeout=0.1)
                continue

            if self.debug:
                p('lidar distance:' ,dist)
                pass
            self.value = dist
            sleep(0.01)


if __name__ == '__main__':
    enable_p()
    ports = serial_ports('ttyUSB')
    # print(ports)
    if len(ports) == 0:
        p(1, 'No serial connection detected')
        exit()
    lidar = TFMiniLidar(ports[0], debug=1)
    input('')
    
