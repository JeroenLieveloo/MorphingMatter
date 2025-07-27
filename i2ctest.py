import smbus2
import time

bus = smbus2.SMBus(1)
address = 0x08  # Arduino I2C address

time.sleep(1)  # Let Arduino boot

# List of (servo_index, actuation) commands
commands = [(0, 10), (1, 50), (2, 200)]

# Flatten to [0, 10, 1, 50, 2, 200]
data = [byte for pair in commands for byte in pair]

# Pad if needed to avoid exceeding 32 bytes total
if len(data) > 31:
    raise ValueError("Too many servo commands for one I2C message.")

try:
    bus.write_i2c_block_data(address, 0x00, data)
    print("Sent commands:", commands)
except Exception as e:
    print("I2C write failed:", e)
