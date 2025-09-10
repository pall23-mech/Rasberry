# button_rpigpio_test.py
import RPi.GPIO as GPIO, time
GPIO.setmode(GPIO.BCM)
PIN = 23
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def handler(pin):
    print(f"Edge on GPIO{pin}, state={GPIO.input(pin)}")

GPIO.add_event_detect(PIN, GPIO.RISING, callback=handler, bouncetime=150)

print("Press the button on GPIO20… (Ctrl+C to exit)")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
