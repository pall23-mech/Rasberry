#!/usr/bin/env python3
# oled_two_buttons_with_leds_safe.py — SSD1306 OLED + 2 buttons (17,23) + 2 LEDs (5,6)

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
PIN_BTN_MODE   = 17   # MODE button
PIN_BTN_ESTOP  = 23   # ESTOP button
PIN_LED_MODE   = 5    # MODE LED  (moved off 22 to avoid conflicts)
PIN_LED_ESTOP  = 6    # ESTOP LED (moved off 25 to avoid conflicts)

# Allow/disallow MODE LED during ESTOP (set False if you want both LEDs on together)
SUPPRESS_MODE_IN_ESTOP = True

# -------- OLED (I2C) --------
I2C_ADDR = 0x3C  # change to 0x3D if your module uses that address
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

led_mode  = LED(PIN_LED_MODE,  pin_factory=factory)
led_estop = LED(PIN_LED_ESTOP, pin_factory=factory)

# -------- FSM --------
class State(Enum):
    IDLE = auto()
    SWITCH_TEST = auto()
    ESTOP = auto()

MODES = [State.SWITCH_TEST, State.IDLE]
mode_index = 0
state = MODES[mode_index]

# Non-blocking LED timers
mode_until  = 0.0
estop_until = 0.0
LED_HOLD_SEC = 1.0

# Track edges so we only log when state changes
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
        set_state(MODES[mode_index])  # restore last mode; don't advance
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

        # MODE LED window
        if now < mode_until and (state != State.ESTOP or not SUPPRESS_MODE_IN_ESTOP):
            if not mode_vis_on:
                mode_vis_on = True
                led_mode.on()
                log_line("MODE LED ON")
        else:
            if mode_vis_on:
                mode_vis_on = False
                if led_mode.is_lit: led_mode.off()
                log_line("MODE LED OFF")

        # ESTOP LED window — always allowed
        if now < estop_until:
            if not estop_vis_on:
                estop_vis_on = True
                led_estop.on()
                log_line("ESTOP LED ON")
        else:
            if estop_vis_on:
                estop_vis_on = False
                if led_estop.is_lit: led_estop.off()
                log_line("ESTOP LED OFF")

        # Optional extra guard: keep MODE LED off during ESTOP when suppression enabled
        if SUPPRESS_MODE_IN_ESTOP and state == State.ESTOP and led_mode.is_lit:
            led_mode.off()

        sleep(0.01)
finally:
    led_mode.off()
    led_estop.off()
    with canvas(oled): pass
