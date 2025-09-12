#!/usr/bin/env python3
from time import sleep
from gpiozero import LED
from gpiozero.pins.lgpio import LGPIOFactory

factory = LGPIOFactory()

PIN_LED_MODE  = 22  # BCM
PIN_LED_ESTOP = 24  # BCM

led_mode  = LED(PIN_LED_MODE,  pin_factory=factory)   # becomes OUTPUT
led_estop = LED(PIN_LED_ESTOP, pin_factory=factory)   # becomes OUTPUT

print("Setting GPIO 22 and 24 to OUTPUT and turning them ON for 2s...")
led_mode.on()
led_estop.on()
sleep(2)

print("Turning them OFF...")
led_mode.off()
sleep(0.5)

print("Blink test (5 times)...")
for _ in range(5):
    led_mode.toggle()
    led_estop.toggle()
    sleep(0.3)

print("Done. Pins remain configured as OUTPUT while this process runs.")
