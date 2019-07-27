from time import sleep
from RPi.GPIO import GPIO

GPIO_PPM = 3

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_PPM, GPIO.OUT)

if __name__ == "__main__":
    while 1:
        GPIO.output(GPIO_PPM, True)
        sleep(0.001)
        GPIO.output(GPIO_PPM, False)
        sleep(0.001)

        
