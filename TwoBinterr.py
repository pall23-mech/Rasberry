# two_buttons_gz.py
from gpiozero import Button
from gpiozero.pins.lgpio import LGPIOFactory
from signal import pause
from time import strftime

factory = LGPIOFactory()

BTN1_PIN = 20
BTN2_PIN = 21

# pull_up=False enables internal pull-down; pressed=True when pin goes HIGH
btn1 = Button(BTN1_PIN, pull_up=False, pin_factory=factory, bounce_time=0.15)
btn2 = Button(BTN2_PIN, pull_up=False, pin_factory=factory, bounce_time=0.15)

def on_press(name):   print(f"[{strftime('%H:%M:%S')}] {name} PRESSED")
def on_release(name): print(f"[{strftime('%H:%M:%S')}] {name} RELEASED")

btn1.when_pressed  = lambda: on_press("Button1 (GPIO20)")
btn1.when_released = lambda: on_release("Button1 (GPIO20)")
btn2.when_pressed  = lambda: on_press("Button2 (GPIO21)")
btn2.when_released = lambda: on_release("Button2 (GPIO21)")

print("Watching buttons on GPIO20 & GPIO21… (Ctrl+C to exit)")
pause()
