#Libraries
from threading import Thread
import RPi.GPIO as GPIO
import time


class UtralSonic(Thread):

    def __init__(self, trigPin = 3, echoPin = 5):
        Thread.__init__(self)
        self.daemon = 1
        self.trigPin = trigPin
        self.echoPin = echoPin
        self.value = 0
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.trigPin, GPIO.OUT)
        GPIO.setup(self.echoPin, GPIO.IN)

    def run(self):
        while 1:
            # set Trigger to HIGH
            GPIO.output(self.trigPin, True)

            # set Trigger after 0.01ms to LOW
            time.sleep(0.00001)
            GPIO.output(self.trigPin, False)

            StartTime = time.time()
            StopTime = time.time()

            # save StartTime
            while GPIO.input(self.echoPin) == 0:
                StartTime = time.time()

            # save time of arrival
            while GPIO.input(self.echoPin) == 1:
                StopTime = time.time()

            # time difference between start and arrival
            TimeElapsed = StopTime - StartTime
            # multiply with the sonic speed (34300 cm/s)
            # and divide by 2, because there and back
            self.value = TimeElapsed * 17150
            time.sleep(0.1)
            print(self.value)



if __name__ == '__main__':
    a = UtralSonic()
    a.start()
    b = input('')
