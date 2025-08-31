import time
import board
import busio
import adafruit_tcs34725

# Set up I2C and sensor
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_tcs34725.TCS34725(i2c)

# Optional tuning
sensor.integration_time = 100   # ms (typical: 50–154; higher = more light gathered)
sensor.gain = 4                 # 1, 4, 16, or 60

# If your breakout has an onboard LED you can toggle:
try:
    sensor.led_current = adafruit_tcs34725.LED_CURRENT_12MA
    sensor.enable = True
except Exception:
    pass  # some boards don't expose LED control

print("Press Ctrl+C to stop.")
try:
    while True:
        r, g, b, c = sensor.color_raw     # raw channels
        ct = sensor.color_temperature     # Kelvin (may be None under some lighting)
        lux = sensor.lux                  # approximate lux
        rgb = sensor.color_rgb_bytes      # 8-bit RGB tuple

        print(f"Raw RGBC: {r:5} {g:5} {b:5} {c:5} | RGB: {rgb} | CT: {ct} K | Lux: {lux}")
        time.sleep(0.5)
except KeyboardInterrupt:
    pass

