import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Define pins
button1_pin = 20
button2_pin = 21

# Set up pins as input with internal pull-down resistors
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print("Press buttons (CTRL+C to exit)")

try:
    while True:
        button1_state = GPIO.input(button1_pin)
        button2_state = GPIO.input(button2_pin)

        print(f"Button1: {button1_state}, Button2: {button2_state}")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting program...")

finally:
    GPIO.cleanup()
