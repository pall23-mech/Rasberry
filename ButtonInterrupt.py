import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
BTN1 = 20
GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def handler(pin):
    print(f"Edge detected on GPIO{pin}, state={GPIO.input(pin)}")

GPIO.add_event_detect(BTN1, GPIO.BOTH, callback=handler, bouncetime=150)

print("Press the button on GPIO20...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
