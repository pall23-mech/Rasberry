#!/usr/bin/env python3
# rover_control.py — FSM + non-blocking LED timers + terminal output

from enum import Enum, auto
from time import monotonic, strftime, sleep
from signal import signal, SIGINT
from gpiozero import Button, LED
from gpiozero.pins.lgpio import LGPIOFactory

factory = LGPIOFactory()

# --- Pins (BCM numbering) ---
PIN_BTN_MODE  = 20  # Button (MODE)
PIN_BTN_ESTOP = 21  # Button (ESTOP)
PIN_LED_MODE  = 16  # LED (MODE)   -> physical pin 36
PIN_LED_ESTOP = 26  # LED (ESTOP)  -> physical pin 37

btn_mode  = Button(PIN_BTN_MODE,  pull_up=False, bounce_time=0.05, pin_factory=factory)
btn_estop = Button(PIN_BTN_ESTOP, pull_up=False, bounce_time=0.05, pin_factory=factory)

led_mode  = LED(PIN_LED_MODE,  pin_factory=factory)
led_estop = LED(PIN_LED_ESTOP, pin_factory=factory)

# --- FSM ---
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
    print(f"[{strftime('%H:%M:%S')}] MODE -> {name}")

def set_state(new_state: State):
    global state
    if state != new_state:
        state = new_state
        show_mode(state.name.replace("_", " "))

def cycle_mode():
    global mode_index
    if state == State.ESTOP:
        # If in ESTOP, restore the last mode (no advance)
        set_state(MODES[mode_index])
        return
    mode_index = (mode_index + 1) % len(MODES)
    set_state(MODES[mode_index])

def press_mode():
    pulse_mode_led()
    cycle_mode()

def press_estop():
    # Pulse the ESTOP LED and immediately enter ESTOP
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

# --- Main loop ---
running = True
def handle_sigint(sig, frame):
    global running
    running = False
signal(SIGINT, handle_sigint)

print("rover-control running. Press MODE to cycle, ESTOP to e-stop. Ctrl+C to exit.")

try:
    while running:
        now = monotonic()

        # MODE LED window — suppressed during ESTOP
        if now < led_mode_until and state != State.ESTOP:
            if not led_mode.is_lit:
                led_mode.on()
                print(f"[{strftime('%H:%M:%S')}] MODE LED ON")
        else:
            if led_mode.is_lit:
                led_mode.off()
                print(f"[{strftime('%H:%M:%S')}] MODE LED OFF")

        # ESTOP LED window — allowed even during ESTOP so you see the pulse
        if now < led_estop_until:
            if not led_estop.is_lit:
                led_estop.on()
                print(f"[{strftime('%H:%M:%S')}] ESTOP LED ON")
        else:
            if led_estop.is_lit:
                led_estop.off()
                print(f"[{strftime('%H:%M:%S')}] ESTOP LED OFF")

        # In ESTOP, keep MODE LED off; ESTOP LED is already handled by its timer above
        if state == State.ESTOP:
            if led_mode.is_lit:
                led_mode.off()

        sleep(0.01)
finally:
    led_mode.off()
    led_estop.off()
    print("Exiting rover-control.")
