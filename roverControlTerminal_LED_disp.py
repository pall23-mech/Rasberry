#!/usr/bin/env python3
# rover_control.py — FSM + non-blocking LED timers + terminal + SSD1306 OLED log

from enum import Enum, auto
from time import monotonic, strftime, sleep
from signal import signal, SIGINT
from collections import deque

from gpiozero import Button, LED
from gpiozero.pins.lgpio import LGPIOFactory

# --- OLED / SSD1306 ---
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont

factory = LGPIOFactory()

# ---------------- Pins (BCM) ----------------
PIN_BTN_MODE   = 23
PIN_BTN_ESTOP  = 24
PIN_LED_MODE   = 22
PIN_LED_ESTOP  = 25

btn_mode  = Button(PIN_BTN_MODE,  pull_up=False, bounce_time=0.05, pin_factory=factory)
btn_estop = Button(PIN_BTN_ESTOP, pull_up=False, bounce_time=0.05, pin_factory=factory)

led_mode  = LED(PIN_LED_MODE,  pin_factory=factory)
led_estop = LED(PIN_LED_ESTOP, pin_factory=factory)

# ---------------- OLED setup ----------------
# Most SSD1306 0.96" I2C modules use address 0x3C; if yours is 0x3D, change below.
try:
    serial = i2c(port=1, address=0x3C)
    oled = ssd1306(serial, width=128, height=64)
except Exception as e:
    oled = None
    print(f"[OLED] init failed: {e}")

# Use a readable default bitmap font
font = ImageFont.load_default()

# Simple scrolling log: keep last N lines and draw each loop
LOG_LINES = 6
log = deque(maxlen=LOG_LINES)

def log_line(text: str):
    ts = strftime('%H:%M:%S')
    msg = f"[{ts}] {text}"
    print(msg)
    log.append(msg)
    draw_oled()

def draw_oled():
    if not oled:
        return
    with canvas(oled) as draw:
        # top-left margin
        x, y = 0, 0
        for line in log:
            draw.text((x, y), line, font=font, fill=255)
            y += 10  # ~6-8px tall font; 10 gives nice spacing

# Clear display at start
def clear_oled():
    if oled:
        with canvas(oled) as draw:
            pass

clear_oled()
log_line("rover-control starting...")

# ---------------- FSM ----------------
class State(Enum):
    IDLE = auto()
    SWITCH_TEST = auto()
    ESTOP = auto()

MODES = [State.SWITCH_TEST, State.IDLE]
mode_index = 0
state = MODES[mode_index]

# Non-blocking LED timers
led_mode_until  = 0.0
led_estop_until = 0.0
LED_HOLD_SEC = 1.0

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
        set_state(MODES[mode_index])
        return
    mode_index = (mode_index + 1) % len(MODES)
    set_state(MODES[mode_index])

def press_mode():
    pulse_mode_led()
    cycle_mode()

def press_estop():
    pulse_estop_led()
    set_state(State.ESTOP)

def pulse_mode_led():
    global led_mode_until
    led_mode_until = monotonic() + LED_HOLD_SEC

def pulse_estop_led():
    global led_estop_until
    led_estop_until = monotonic() + LED_HOLD_SEC

btn_mode.when_pressed  = press_mode
btn_estop.when_pressed = press_estop

show_mode(state.name.replace("_", " "))

# ---------------- Main loop ----------------
running = True
def handle_sigint(sig, frame):
    global running
    running = False
signal(SIGINT, handle_sigint)

log_line("Press MODE to cycle, ESTOP to e-stop. Ctrl+C to exit.")

try:
    while running:
        now = monotonic()

        # MODE LED window — suppressed during ESTOP
        if now < led_mode_until and state != State.ESTOP:
            if not led_mode.is_lit:
                led_mode.on()
                log_line("MODE LED ON")
        else:
            if led_mode.is_lit:
                led_mode.off()
                log_line("MODE LED OFF")

        # ESTOP LED window — allowed even during ESTOP so you see the pulse
        if now < led_estop_until:
            if not led_estop.is_lit:
                led_estop.on()
                log_line("ESTOP LED ON")
        else:
            if led_estop.is_lit:
                led_estop.off()
                log_line("ESTOP LED OFF")

        # In ESTOP, keep MODE LED off; ESTOP LED handled by timer
        if state == State.ESTOP and led_mode.is_lit:
            led_mode.off()
            # (no log here; already logged OFF in the section above)

        # Refresh OLED periodically even if nothing changed (optional)
        # draw_oled()

        sleep(0.01)
finally:
    led_mode.off()
    led_estop.off()
    log_line("Exiting rover-control.")
    # leave the last screen up; if you prefer blanking:
    # clear_oled()
