from time import sleep
from RPi import GPIO

GPIO_PPM = 3

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_PPM, GPIO.OUT)

if __name__ == "__main__":
    try:
        while 1:
            GPIO.output(GPIO_PPM, True)
            sleep(0.001)
            GPIO.output(GPIO_PPM, False)
            sleep(0.001)
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
