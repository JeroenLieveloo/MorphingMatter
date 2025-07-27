import smbus2
import sys

class Arduino:
    def __init__(self, actuators, address, bus_num=1):
        self.isConnected = False
        self.actuators = actuators  # List of Actuator objects
        self.address = address
        if address > 255:
            print(f"Cannot convert {address} to byte because it is larger than 255.")

        try:
            print("Connecting to Arduino via I2C at address", self.address, file=sys.stderr)
            self.init_bus(bus_num)
            if not self.isConnected: return
            print("Connected to Arduino at address", self.address, file=sys.stderr)
            self.address = address  # Use address as address for I2C
        except Exception as e:
            print(f"Failed to initialize Arduino: {e}", file=sys.stderr)
            self.close()

    def get_actuators(self):
        return self.actuators

    def add_actuator(self, actuator):
        self.actuators.append(actuator)

    def get_pins(self):
        pins = []
        for actuator in self.actuators:
            if actuator.arduino == self.address:
                pins.append(actuator.pin)
        return pins
    
    def init_bus(self, bus_num):
        try:
            self.bus = smbus2.SMBus(bus_num)
            self.isConnected = True
        except Exception as e:
            print("Could not connect I2C bus: ", e, file=sys.stderr)
            self.bus = None
            self.isConnected = False
        

    def write(self, data):
        """
        Sends an array of (pin, value) pairs to the Arduino over I2C.
        :param data: List of tuples, where each tuple is (pin, value)
        """
        #if not connected to i2c, skip sending the data and write it to the console instead
        if not self.isConnected: 
            print(f"not connected... data: {data}")
            return
        # Flatten to [0, 10, 1, 50, 2, 200]
        message = [byte for pair in data for byte in pair]

        try:
            # Pad if needed to avoid exceeding 32 bytes total
            if len(message) > 31:
                raise ValueError("Too many servo commands for one I2C message.")
            self.bus.write_i2c_block_data(self.address, 0x00, message)
            #print("Sent commands:", commands)
        except Exception as e:
            print(f"Arduino {self.address} I2C write error: {e}", file=sys.stderr)


    def close(self):
        if hasattr(self, 'bus') and self.bus is not None:
            try:
                self.bus.close()
            except Exception as e:
                print("Can't close bus:", e, file=sys.stderr)
