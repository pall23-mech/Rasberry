#!/usr/bin/env python3
import time
from smbus2 import SMBus

# ICM-20948 constants (Bank 0 unless noted)
REG_BANK_SEL      = 0x7F  # write 0x00 for Bank 0
WHO_AM_I          = 0x00  # expect 0xEA
PWR_MGMT_1        = 0x06  # wake/sleep, clock
PWR_MGMT_2        = 0x07  # enable/disable accel/gyro axes (0=enabled)
ACCEL_XOUT_H      = 0x2D  # XH,XL,YH,YL,ZH,ZL
GYRO_XOUT_H       = 0x33  # XH,XL,YH,YL,ZH,ZL
TEMP_OUT_H        = 0x39  # TH,TL

WHO_AM_I_EXPECT   = 0xEA
I2C_BUS           = 1
POSSIBLE_ADDRS    = [0x68, 0x69]   # AD0=0 -> 0x68, AD0=1 -> 0x69

def to_int16(high, low):
    v = (high << 8) | low
    return v - 0x10000 if v & 0x8000 else v

class ICM20948:
    def __init__(self, bus_num=I2C_BUS):
        self.bus = SMBus(bus_num)
        self.addr = self._find_addr()
        self._select_bank(0x00)               # Bank 0
        self._wake_and_enable()

    def _find_addr(self):
        # Probe both typical addresses and verify WHO_AM_I
        for a in POSSIBLE_ADDRS:
            try:
                self.bus.write_byte_data(a, REG_BANK_SEL, 0x00)  # Bank 0
                who = self.bus.read_byte_data(a, WHO_AM_I)
                if who == WHO_AM_I_EXPECT:
                    return a
            except OSError:
                continue
        raise RuntimeError("ICM-20948 not found on 0x68/0x69 or WHO_AM_I mismatch.")

    def _select_bank(self, bank_val):
        # 0x00 for Bank 0; other banks are 0x10,0x20,0x30 (not needed here)
        self.bus.write_byte_data(self.addr, REG_BANK_SEL, bank_val & 0x30)

    def _wake_and_enable(self):
        # Clear sleep, select best clock source (auto)
        self.bus.write_byte_data(self.addr, PWR_MGMT_1, 0x01)  # CLKSEL=1, SLEEP=0
        time.sleep(0.010)
        # Enable accel+gyro on all axes (0x00 = all enabled)
        self.bus.write_byte_data(self.addr, PWR_MGMT_2, 0x00)
        time.sleep(0.010)

    def read_accel(self):
        data = self.bus.read_i2c_block_data(self.addr, ACCEL_XOUT_H, 6)
        ax = to_int16(data[0], data[1])
        ay = to_int16(data[2], data[3])
        az = to_int16(data[4], data[5])
        return ax, ay, az

    def read_gyro(self):
        data = self.bus.read_i2c_block_data(self.addr, GYRO_XOUT_H, 6)
        gx = to_int16(data[0], data[1])
        gy = to_int16(data[2], data[3])
        gz = to_int16(data[4], data[5])
        return gx, gy, gz

    def read_temp_c(self):
        th, tl = self.bus.read_i2c_block_data(self.addr, TEMP_OUT_H, 2)
        raw = to_int16(th, tl)
        # InvenSense 20xx family temp conversion (datasheet/guides use this form)
        # T(°C) ≈ (raw / 333.87) + 21.0
        return (raw / 333.87) + 21.0

    def close(self):
        try:
            self.bus.close()
        except Exception:
            pass

def main():
    imu = ICM20948()
    print(f"ICM-20948 found at I2C 0x{imu.addr:02X}, reading every 2s. Ctrl+C to stop.")
    try:
        while True:
            ax, ay, az = imu.read_accel()
            gx, gy, gz = imu.read_gyro()
            tc = imu.read_temp_c()
            print(f"Accel: ({ax}, {ay}, {az})  Gyro: ({gx}, {gy}, {gz})  Temp: {tc:.2f} °C")
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        imu.close()

if __name__ == "__main__":
    main()

