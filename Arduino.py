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
            #print(data)
            return
        message = self.serialize_data(data)
        # Convert message to bytes and send over I2C
        try:
            # Send each byte separately (I2C block write is limited)
            for b in message:
                self.bus.write_byte(self.address, b)
        except Exception as e:
            print(f"Arduino {self.address} I2C write error: {e}", file=sys.stderr)

    def serialize_data(self, data):
        """
        Converts the list of (pin, value) tuples into a byte array.
        :param data: List of tuples (pin, value)
        :return: Byte array
        """
        # Example: [pin, value, pin, value, ...]
        byte_data = []
        for pin, value in data:
            byte_data.append(int(pin))
            # Scale value to 0-255 if needed
            byte_data.append(int(max(0, min(255, int(value * 255)))))
        return byte_data

    def close(self):
        if hasattr(self, 'bus') and self.bus is not None:
            try:
                self.bus.close()
            except Exception as e:
                print("Can't close bus:", e, file=sys.stderr)
