import time
import smbus2

# ICM-2904B default I2C address (double-check your module’s docs/datasheet)
ICM2904B_ADDR = 0x68  

# I²C bus (1 for Raspberry Pi)
bus = smbus2.SMBus(1)

# --- Helper: read 16-bit signed value from two registers ---
def read_word(register):
    high = bus.read_byte_data(ICM2904B_ADDR, register)
    low  = bus.read_byte_data(ICM2904B_ADDR, register + 1)
    value = (high << 8) | low
    if value & 0x8000:  # convert to signed
        value -= 65536
    return value

# --- Example register map (adjust for ICM-2904B datasheet) ---
REG_ACCEL_XOUT_H = 0x3B
REG_GYRO_XOUT_H  = 0x43
REG_TEMP_OUT_H   = 0x41
# (Magnetometer is usually via secondary I²C passthrough; check datasheet)

def read_all():
    # Accel
    ax = read_word(REG_ACCEL_XOUT_H)
    ay = read_word(REG_ACCEL_XOUT_H + 2)
    az = read_word(REG_ACCEL_XOUT_H + 4)

    # Temp
    temp_raw = read_word(REG_TEMP_OUT_H)
    temp_c = (temp_raw / 333.87) + 21.0  # check datasheet for conversion

    # Gyro
    gx = read_word(REG_GYRO_XOUT_H)
    gy = read_word(REG_GYRO_XOUT_H + 2)
    gz = read_word(REG_GYRO_XOUT_H + 4)

    return {
        "accel": (ax, ay, az),
        "gyro": (gx, gy, gz),
        "temp_c": temp_c
    }

# --- Main loop ---
try:
    while True:
        data = read_all()
        print(f"Accel: {data['accel']}, Gyro: {data['gyro']}, Temp: {data['temp_c']:.2f}°C")
        time.sleep(2)  # every 2 seconds
except KeyboardInterrupt:
    print("Stopping...")
    bus.close()
