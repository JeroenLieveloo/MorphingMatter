import sys
import json
import csv
import math
import time
import select
import get_devices

arduinos = []
actuators = []
speed = 1 #actuation per second
strength = 1
size = 3
max_speed = 0.2
x, y = 1, 1
mode = "release"
hold = False

iteration_duration = 1
last_iteration = time.time()

class Arduino:
    def __init__(self, port):
        try:
            print("Connecting to arduino on port", port, file=sys.stderr)
            self.port = port # port the arduino is connected to
            self.connection = get_devices.connect(port)
            print("Connected to arduino", self.connection, file=sys.stderr)
            self.UID = get_devices.identify_arduino(port) # name of the arduino
            print("New Arduino:", port, self.UID, file=sys.stderr)
        except:
            print("failed to initialize arduino:", file=sys.stderr)
            self.close()

    def get_pins(self):
        pins = []
        for actuator in actuators:
            if actuator.arduino == self.UID:
                pins.append(actuator.pin)
        return pins

    def write(self, data):
        """
        Sends an array of (pin, value) pairs to the Arduino.
        :param data: List of tuples, where each tuple is (pin, value)
        """
        message = self.serialize_data(data)
        self.connection.write(message.encode('utf-8'))

    def serialize_data(self, data):
        """
        Converts the list of (pin, value) tuples into a string message.
        :param data: List of tuples (pin, value)
        :return: Serialized string
        """
        return ','.join(f'{pin}:{value}' for pin, value in data) + '\n'

    def close(self):
        self.connection.close()

class Actuator:
    def __init__(self, arduino, pin, x, y):
        #print("new actuator:", arduino, pin, x, y, file=sys.stderr)
        self.arduino = arduino # UID of the arduino
        self.pin = pin # pin number the actuator is connected to on the arduino
        self.x = x #x position
        self.y = y #y position
        self.actuation = 0.5
        self.pressure = 0.5

    def set_actuation(self, input):
        # Sets the actuation, but restricts it to be between 0-1 and limits its change
        desired = min(1, max(0, input))
        diff = desired - self.actuation
        change_limit = max_speed * iteration_duration
        change_magnitude = min(abs(diff), change_limit)
        self.actuation += math.copysign(change_magnitude, diff)
 
    def increase_actuation(self, input):
        # Increases actuation in input per second
        self.set_actuation(self.actuation + input * speed *iteration_duration)

    def decrease_actuation(self, input):
        # Decreases actuation in input per second
        self.increase_actuation(-input)


    def release(self):
        self.actuation += (0.5-self.actuation) * speed * iteration_duration

    def static(self, value):
        self.set_actuation(value)

    def push(self, cursor_x, cursor_y):
        self.decrease_actuation(self.calc_effect(cursor_x, cursor_y))

    def pull(self, cursor_x, cursor_y):
        self.increase_actuation(self.calc_effect(cursor_x, cursor_y))
    
    def ripple(self, x, y):
        dist = self.calc_dist(x, y)
        ripple = self.calc_sin(dist)
        self.set_actuation(ripple * strength)


    def calc_dist(self, cursor_x, cursor_y):
        return math.sqrt((cursor_x - self.x)**2 + (cursor_y - self.y)**2)
    
    def calc_sin(self, dist):
        val = last_iteration * speed * 0.3 + dist/size
        rads = val * math.pi
        return (math.sin(rads) + 1) * 0.5

    def calc_effect(self, cursor_x, cursor_y):
        dist = self.calc_dist(cursor_x, cursor_y)
        return strength * (1 - (dist/size))


def set_arduinos():
    devices = get_devices.get_connected_devices()
    arduinos = []
    if devices:
        for device in devices:
            print(f"Device Name: {device['device_name']}, COM Port: {device['com_port']}, Serial Number: {device['serial_number']}", file=sys.stderr, flush=True)
            arduinos.append(Arduino(device['com_port']))
    else:
        print("No USB devices found.",file=sys.stderr, flush=True)


def calc_iteration_duration():
    #returns delta time in seconds
    global last_iteration
    global iteration_duration
    delta_time = time.time() - last_iteration
    last_iteration = time.time()
    iteration_duration = delta_time

def load_config(filename):
    with open(filename, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            x, y, pin, arduino = float(row[0]), float(row[1]), int(row[2]), str(row[3])
            actuators.append(Actuator(arduino, pin, x, y))

def read_data():
    global speed, strength, size, max_speed, x, y, mode, hold
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        input_data = sys.stdin.readline().strip()
        if input_data:
            data = json.loads(input_data)
            if 'x' in data and 'y' in data:
                x, y = data['x'], data['y']
            
            if 'speed' in data:
                speed = float(data['speed'])
                print("set speed to:", speed, file=sys.stderr)
            
            if 'size' in data:
                size = float(data['size'])
                print("set size to:", size, file=sys.stderr)
            
            if 'strength' in data:
                strength = float(data['strength'])
                print("set str to:", strength, file=sys.stderr)
            
            if 'mode' in data:
                mode = data['mode']
                print("set mode to:", mode, file=sys.stderr)

            if 'hold' in data:
                hold = bool(data['hold'])
                print("set hold to:", hold, file=sys.stderr)
            
            if 'max_speed' in data:
                max_speed = float(data['max_speed'])
                print("set max_speed to:", max_speed, file=sys.stderr)

def calc_actuation():
    actuator_values = []
    for actuator in actuators:
        if not hold:
            match mode:
                case "release":
                    actuator.release()

                case "static":
                    actuator.static(abs(y))

                case "push":
                    actuator.push(x, y)
                    
                case "pull":
                    actuator.pull(x, y)

                case "ripple":
                    actuator.ripple(x, y)
                
        value = {"pressure": actuator.pressure, "actuation": actuator.actuation}
        value.update({'x': actuator.x, 'y': actuator.y, 'pin': actuator.pin})
        actuator_values.append(value)
    
    return actuator_values

def update_client(data):
    print(data,file=sys.stdout, flush=True)

def update_actuators():
    for arduino in arduinos:
        data = []
        for actuator in actuators:
            if actuator.arduino == arduino.UID:
                data.append((actuator.pin, actuator.actuation))
        arduino.write(data)


def main():
    global speed, strength, size, max_speed, x, y, mode, hold

    # Load the actuator configuration
    load_config('config.csv')
    set_arduinos()
    while(True):
        try:
            time.sleep(0.05)
            calc_iteration_duration()
            read_data()
            actuator_values = calc_actuation()
            update_client(json.dumps(actuator_values))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
