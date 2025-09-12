#!/usr/bin/env python3
# oled_two_buttons_one_diode.py — SSD1306 OLED + 2 buttons (17,23) + ONE LED on BCM22

from enum import Enum, auto
from time import monotonic, strftime, sleep
from signal import signal, SIGINT
from collections import deque
from threading import Lock

from gpiozero import Button, LED
from gpiozero.pins.lgpio import LGPIOFactory

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont

# -------- Pins (BCM) --------
PIN_BTN_MODE  = 17       # MODE button
PIN_BTN_ESTOP = 23       # ESTOP button
PIN_LED       = 26       # Single diode/LED output

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
        lines = list(log)  # snapshot to avoid "deque mutated during iteration"
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

# -------- Hardware --------
factory = LGPIOFactory()

# NOTE: pull_up=False assumes your buttons connect to 3V3 when pressed.
# If your buttons connect to GND when pressed, change both to pull_up=True.
btn_mode  = Button(PIN_BTN_MODE,  pull_up=False, bounce_time=0.05, pin_factory=factory)
btn_estop = Button(PIN_BTN_ESTOP, pull_up=False, bounce_time=0.05, pin_factory=factory)

# Single diode on BCM22 (active-high)
led = None
try:
    led = LED(PIN_LED, pin_factory=factory)
    log_line(f"Diode/LED on BCM{PIN_LED} ready.")
except Exception as e:
    log_line(f"LED init failed on BCM{PIN_LED}: {e} (continuing without physical LED).")

# -------- FSM (same as before, but both buttons pulse the single diode) --------
class State(Enum):
    IDLE = auto()
    SWITCH_TEST = auto()
    ESTOP = auto()

MODES = [State.SWITCH_TEST, State.IDLE]
mode_index = 0
state = MODES[mode_index]

# One non-blocking timer for the diode
diode_until = 0.0
LED_HOLD_SEC = 1.0
diode_on_vis = False  # for edge logging

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

def pulse_diode():
    global diode_until
    diode_until = monotonic() + LED_HOLD_SEC

def press_mode():
    pulse_diode()
    cycle_mode()

def press_estop():
    pulse_diode()
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
log_line_(f"Buttons MODE={PIN_BTN_MODE}, ESTOP={PIN_BTN_ESTOP}; Diode on BCM{PIN_LED}")
log_line("Press a button to pulse the diode. Ctrl+C to exit.")

try:
    while running:
        now = monotonic()

        # Single diode pulse window (works for both buttons, even during ESTOP)
        if now < diode_until:
            if not diode_on_vis:
                diode_on_vis = True
                if led: led.on()
                log_line("DIODE ON")
        else:
            if diode_on_vis:
                diode_on_vis = False
                if led and led.is_lit: led.off()
                log_line("DIODE OFF")

        sleep(0.01)
finally:
    if led:
        led.off()
    with canvas(oled): pass
