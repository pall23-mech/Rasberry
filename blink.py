import RPi.GPIO as GPIO
import time

# Use BCM numbering (GPIO17 = pin 11)
LED_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

print("Press CTRL+C to stop")

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)  # LED on
        time.sleep(1)                   # wait 1 second
        GPIO.output(LED_PIN, GPIO.LOW)   # LED off
        time.sleep(1)                   # wait 1 second
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
