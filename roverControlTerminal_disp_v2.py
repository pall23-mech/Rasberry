#!/usr/bin/env python3
# oled_two_buttons_ledlogic.py — SSD1306 OLED + 2 buttons (17,23), no LEDs.
# Shows non-blocking "LED" pulses on the display instead of driving GPIO.

from enum import Enum, auto
from time import monotonic, strftime, sleep
from signal import signal, SIGINT
from collections import deque

from gpiozero import Button
from gpiozero.pins.lgpio import LGPIOFactory

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont

# -------- Pins (BCM) --------
PIN_BTN_MODE  = 17   # MODE button (works for you)
PIN_BTN_ESTOP = 23   # ESTOP button (moved from 27)

# -------- OLED (I2C) --------
I2C_ADDR = 0x3C  # change to 0x3D if needed
serial = i2c(port=1, address=I2C_ADDR)
oled = ssd1306(serial, width=128, height=64)
font = ImageFont.load_default()

LOG_LINES = 6
log = deque(maxlen=LOG_LINES)

def draw_oled():
    with canvas(oled) as draw:
        y = 0
        for line in log:
            draw.text((0, y), line, font=font, fill=255)
            y += 10

def log_line(text: str):
    msg = f"[{strftime('%H:%M:%S')}] {text}"
    print(msg)
    log.append(msg)
    draw_oled()

# -------- Buttons --------
# Use pull_up=False if the button connects to 3V3 when pressed.
# If your button goes to GND when pressed, change to pull_up=True.
factory = LGPIOFactory()
btn_mode  = Button(PIN_BTN_MODE,  pull_up=False, bounce_time=0.05, pin_factory=factory)
btn_estop = Button(PIN_BTN_ESTOP, pull_up=False, bounce_time=0.05, pin_factory=factory)

# -------- FSM --------
class State(Enum):
    IDLE = auto()
    SWITCH_TEST = auto()
    ESTOP = auto()

MODES = [State.SWITCH_TEST, State.IDLE]
mode_index = 0
state = MODES[mode_index]

# Non-blocking "LED" timers (virtual LEDs shown on OLED)
mode_until  = 0.0
estop_until = 0.0
LED_HOLD_SEC = 1.0

# Track on/off edges so we only log when state changes
mode_vis_on  = False
estop_vis_on = False

def show_mode(name: str):
    log_line(f"MODE -> {name}")

def set_state(new_state: State):
    global state
    if state != new_state:
        state = new_state
        show_mode(state.name.replace("_", " "))

def cycle_mode():
    global mode_index
    if state == State.ESTOP:
        set_state(MODES[mode_index])  # restore last mode
        return
    mode_index = (mode_index + 1) % len(MODES)
    set_state(MODES[mode_index])

def pulse_mode():
    global mode_until
    mode_until = monotonic() + LED_HOLD_SEC

def pulse_estop():
    global estop_until
    estop_until = monotonic() + LED_HOLD_SEC

def press_mode():
    pulse_mode()
    cycle_mode()

def press_estop():
    pulse_estop()
    set_state(State.ESTOP)

btn_mode.when_pressed  = press_mode
btn_estop.when_pressed = press_estop

# -------- Main --------
running = True
def handle_sigint(sig, frame):
    global running
    running = False
signal(SIGINT, handle_sigint)

with canvas(oled): pass
show_mode(state.name.replace("_", " "))
log_line("Press MODE(17) or ESTOP(23). Ctrl+C to exit.")

try:
    while running:
        now = monotonic()

        # MODE "LED" window — suppressed during ESTOP
        if now < mode_until and state != State.ESTOP:
            if not mode_vis_on:
                mode_vis_on = True
                log_line("MODE LED ON")
        else:
            if mode_vis_on:
                mode_vis_on = False
                log_line("MODE LED OFF")

        # ESTOP "LED" window — allowed even during ESTOP
        if now < estop_until:
            if not estop_vis_on:
                estop_vis_on = True
                log_line("ESTOP LED ON")
        else:
            if estop_vis_on:
                estop_vis_on = False
                log_line("ESTOP LED OFF")

        sleep(0.01)
finally:
    with canvas(oled): pass
