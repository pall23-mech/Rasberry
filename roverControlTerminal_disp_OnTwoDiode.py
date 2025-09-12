#!/usr/bin/env python3
# oled_two_buttons_two_diodes_pigpio.py
# SSD1306 OLED + Buttons on 17/23 + TWO diodes on 22/24 (uses PiGPIOFactory)

from enum import Enum, auto
from time import monotonic, strftime, sleep
from signal import signal, SIGINT
from collections import deque
from threading import Lock

from gpiozero import Button, LED
from gpiozero.pins.pigpio import PiGPIOFactory  # pigpio backend

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont

# -------- Pins (BCM) --------
PIN_BTN_MODE   = 17       # MODE button
PIN_BTN_ESTOP  = 23       # ESTOP button
PIN_LED_MODE   = 22       # MODE diode/LED
PIN_LED_ESTOP  = 24       # ESTOP diode/LED

# -------- OLED (I2C) --------
I2C_ADDR = 0x3C
serial = i2c(port=1, address=I2C_ADDR)
oled = ssd1306(serial, width=128, height=64)
font = ImageFont.load_default()

LOG_LINES = 6
log = deque(maxlen=LOG_LINES)
log_lock = Lock()

def draw_oled():
    with log_lock:
        lines = list(log)  # snapshot: avoid "deque mutated during iteration"
    with canvas(oled) as draw:
        y = 0
        for line in lines:
            draw.text((0, y), line, font=font, fill=255)
            y += 10

def log_line(text: str):
    msg = f"[{strftime('%H:%M:%S')}] {text}"
    print(msg)
    with log_lock:
        log.append(msg)
    draw_oled()

# -------- Hardware (pigpio factory) --------
factory = PiGPIOFactory()  # connects to local pigpio daemon

# NOTE: pull_up=False assumes your buttons go to 3V3 when pressed.
# If your buttons go to GND when pressed, change both to pull_up=True.
btn_mode  = Button(PIN_BTN_MODE,  pull_up=False, bounce_time=0.05, pin_factory=factory)
btn_estop = Button(PIN_BTN_ESTOP, pull_up=False, bounce_time=0.05, pin_factory=factory)

# Diodes (active-high). If one fails to init, we continue without it.
led_mode = led_estop = None
try:
    led_mode = LED(PIN_LED_MODE, pin_factory=factory)
    log_line(f"MODE diode ready on BCM{PIN_LED_MODE}.")
except Exception as e:
    log_line(f"MODE diode init failed on BCM{PIN_LED_MODE}: {e}")

try:
    led_estop = LED(PIN_LED_ESTOP, pin_factory=factory)
    log_line(f"ESTOP diode ready on BCM{PIN_LED_ESTOP}.")
except Exception as e:
    log_line(f"ESTOP diode init failed on BCM{PIN_LED_ESTOP}: {e}")

# -------- Minimal FSM & timers --------
class State(Enum):
    IDLE = auto()
    SWITCH_TEST = auto()
    ESTOP = auto()

MODES = [State.SWITCH_TEST, State.IDLE]
mode_index = 0
state = MODES[mode_index]

# Independent non-blocking timers for each diode
mode_until  = 0.0
estop_until = 0.0
LED_HOLD_SEC = 1.0

# Edge flags so we only log on changes
mode_on_vis  = False
estop_on_vis = False

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
        set_state(MODES[mode_index])  # restore last mode; don't advance
        return
    mode_index = (mode_index + 1) % len(MODES)
    set_state(MODES[mode_index])

def pulse_mode_diode():
    global mode_until
    mode_until = monotonic() + LED_HOLD_SEC

def pulse_estop_diode():
    global estop_until
    estop_until = monotonic() + LED_HOLD_SEC

def press_mode():
    pulse_mode_diode()
    cycle_mode()

def press_estop():
    pulse_estop_diode()
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
log_line(f"Buttons MODE={PIN_BTN_MODE}, ESTOP={PIN_BTN_ESTOP}; Diodes MODE={PIN_LED_MODE}, ESTOP={PIN_LED_ESTOP}")
log_line("Press buttons to pulse diodes. Ctrl+C to exit.")

try:
    while running:
        now = monotonic()

        # MODE diode window
        if now < mode_until:
            if not mode_on_vis:
                mode_on_vis = True
                if led_mode: led_mode.on()
                log_line("MODE DIODE ON")
        else:
            if mode_on_vis:
                mode_on_vis = False
                if led_mode and led_mode.is_lit: led_mode.off()
                log_line("MODE DIODE OFF")

        # ESTOP diode window
        if now < estop_until:
            if not estop_on_vis:
                estop_on_vis = True
                if led_estop: led_estop.on()
                log_line("ESTOP DIODE ON")
        else:
            if estop_on_vis:
                estop_on_vis = False
                if led_estop and led_estop.is_lit: led_estop.off()
                log_line("ESTOP DIODE OFF")

        sleep(0.01)
finally:
    if led_mode: led_mode.off()
    if led_estop: led_estop.off()
    with canvas(oled): pass

