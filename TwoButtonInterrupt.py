import RPi.GPIO as GPIO
import signal
import time

# Reset any previous config
GPIO.cleanup()

GPIO.setmode(GPIO.BCM)

BTN1 = 20
BTN2 = 21

GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BTN2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def handle_edge(pin):
    state = GPIO.input(pin)
    if state:
        print(f"GPIO{pin} PRESSED")
    else:
        print(f"GPIO{pin} RELEASED")

GPIO.add_event_detect(BTN1, GPIO.BOTH, callback=handle_edge, bouncetime=150)
GPIO.add_event_detect(BTN2, GPIO.BOTH, callback=handle_edge, bouncetime=150)

print("Watching buttons… (Ctrl+C to exit)")
try:
    signal.pause()
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

