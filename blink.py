import RPi.GPIO as GPIO
import time
USER_LED=23

GPIO.setmode(GPIO.BCM)
GPIO.setup(USER_LED, GPIO.OUT)
try:
    while True:
        GPIO.output(USER_LED, 1)
        time.sleep(0.5)
        GPIO.output(USER_LED, 0)
        time.sleep(0.5)
        print("cycle")
except:
    GPIO.setup(USER_LED, GPIO.IN)
    GPIO.cleanup()