#!/usr/bin/env python3
#Virkar
# oled_button_hello.py — GME12864-12 (SSD1306 I2C) + one button
#
# Wiring (BCM):
#   OLED SDA -> BCM2 (pin 3), SCL -> BCM3 (pin 5), VCC -> 3V3, GND -> GND
#   Button -> BCM23 (pin 16) to 3V3 (since pull_up=False below). If you prefer
#   GPIO-to-GND wiring, set pull_up=True instead and connect the button to GND.

from time import sleep, strftime
from signal import signal, SIGINT

from gpiozero import Button
from gpiozero.pins.lgpio import LGPIOFactory

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont

# -------- Config --------
PIN_BTN = 17          # change if you wired the button elsewhere
I2C_ADDR = 0x3C       # change to 0x3D if your module uses that address

# -------- Init OLED --------
serial = i2c(port=1, address=I2C_ADDR)
oled = ssd1306(serial, width=128, height=64)
font = ImageFont.load_default()

def draw_lines(lines):
    with canvas(oled) as draw:
        y = 0
        for line in lines:
            draw.text((0, y), line, font=font, fill=255)
            y += 10

# -------- Init Button --------
# Using pull_up=False assumes your button pulls the pin HIGH (to 3V3) when pressed.
# If your button goes to GND, set pull_up=True instead.
factory = LGPIOFactory()
btn = Button(PIN_BTN, pull_up=False, bounce_time=0.05, pin_factory=factory)

# -------- Handlers --------
def on_press():
    draw_lines(["Hello, world!", f"@ {strftime('%H:%M:%S')}"])

def on_release():
    draw_lines(["Press the button"])

btn.when_pressed = on_press
btn.when_released = on_release

# -------- Main --------
running = True
def handle_sigint(sig, frame):
    global running
    running = False
signal(SIGINT, handle_sigint)

# Initial screen
draw_lines(["Press the button"])

try:
    while running:
        sleep(0.1)
finally:
    # optional: clear on exit
    with canvas(oled):
        pass
