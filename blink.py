import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)   # use physical pin numbers
LED_PIN = 11               # physical pin 11 == BCM GPIO 17
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

