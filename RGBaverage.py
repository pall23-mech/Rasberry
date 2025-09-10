import time
import board
import busio
import adafruit_tcs34725
from collections import deque

# Set up I2C and sensor
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_tcs34725.TCS34725(i2c)

# Optional tuning
sensor.integration_time = 100   # ms
sensor.gain = 4                 # 1, 4, 16, or 60

# --- Moving average (window = 3) ---
WINDOW = 3
buf = {
    "r": deque(maxlen=WINDOW),
    "g": deque(maxlen=WINDOW),
    "b": deque(maxlen=WINDOW),
    "c": deque(maxlen=WINDOW),
    "lux": deque(maxlen=WINDOW),
    "ct": deque(maxlen=WINDOW),     # may skip None
    "rb": deque(maxlen=WINDOW),     # 8-bit RGB bytes
    "gb": deque(maxlen=WINDOW),
    "bb": deque(maxlen=WINDOW),
}

def push(key, value):
    if value is not None:
        buf[key].append(value)

def mean(key):
    q = buf[key]
    return (sum(q) / len(q)) if q else None

print("Press Ctrl+C to stop.")
try:
    while True:
        r, g, b, c = sensor.color_raw
        ct = sensor.color_temperature     # may be None
        lux = sensor.lux
        rb, gb, bb = sensor.color_rgb_bytes

        # update buffers
        push("r", r);   push("g", g);   push("b", b);   push("c", c)
        push("lux", lux); push("ct", ct)
        push("rb", rb); push("gb", gb); push("bb", bb)

        # compute MA3
        r_m = mean("r"); g_m = mean("g"); b_m = mean("b"); c_m = mean("c")
        lux_m = mean("lux")
        ct_m = mean("ct")   # may be None if not enough valid samples yet
        rb_m = mean("rb"); gb_m = mean("gb"); bb_m = mean("bb")

        # pretty printing with safe fallbacks
        def fmt_int(x):  return "—" if x is None else str(int(round(x)))
        def fmt_f1(x):   return "—" if x is None else f"{x:.1f}"

        print(
            f"Raw RGBC: {r:5} {g:5} {b:5} {c:5}"
            f" | MA3 RGBC: {fmt_int(r_m):>5} {fmt_int(g_m):>5} {fmt_int(b_m):>5} {fmt_int(c_m):>5}"
            f" | RGB: ({rb:3},{gb:3},{bb:3})"
            f" | MA3 RGB: ({fmt_int(rb_m):>3},{fmt_int(gb_m):>3},{fmt_int(bb_m):>3})"
            f" | CT: {('—' if ct is None else str(int(ct)))} K"
            f" | MA3 CT: {fmt_int(ct_m)} K"
            f" | Lux: {lux:.1f}"
            f" | MA3 Lux: {fmt_f1(lux_m)}"
        )

        time.sleep(0.5)   # sampling period; MA3 introduces ~0.5 s effective delay
except KeyboardInterrupt:
    pass
