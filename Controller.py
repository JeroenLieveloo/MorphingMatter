
import sys
import json
import csv
import time
import select
import logging
import math

from Arduino import Arduino 
from Actuator import Actuator
from common import Position, calc_dist

iteration_delay = 0.05


# Command to install module required for I2C:
# pip install smbus2


# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    stream=sys.stderr
)

class Controller:
    def __init__(self):
        self.arduinos = []
        self.actuators = []
        
        self.cursor = Position(0, 0)

        self.speed = 1.0
        self.strength = 1.0
        self.size = 1.0
        self.max_speed = 1.0
        self.volume = 0.5
        self.mode = "pull"
        self.hold = False
        self.pressed = False
        self.equalisation = 0.1

        self.last_iteration = time.time()
        self.iteration_duration = 0.05
        

    def calc_iteration_duration(self):
        delta_time = time.time() - self.last_iteration
        self.last_iteration = time.time()
        self.iteration_duration = delta_time

    def load_config(self, filename):
        self.actuators = []
        adruinoUIDs = []
        with open(filename, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                x, y, pin, arduinoUID = float(row[0]), float(row[1]), int(row[2]), int(row[3])
                self.actuators.append(Actuator(arduinoUID, pin, Position(x, y)))
                if arduinoUID not in adruinoUIDs:
                    adruinoUIDs.append(arduinoUID)

        for arduinoUID in adruinoUIDs:
            arduino_actuators = [actuator for actuator in self.actuators if actuator.arduino == arduinoUID]
            self.arduinos.append(Arduino(arduino_actuators, arduinoUID))
                

                

    def read_data(self):
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            input_data = sys.stdin.readline().strip()
            if input_data:
                data = json.loads(input_data)
                if 'x' in data and 'y' in data:
                    self.cursor = Position(data['x'], data['y'])
                
                if 'volume' in data:
                    self.volume = float(data['volume'])
                    logging.info(f"set volume to: {self.volume}")

                if 'speed' in data:
                    self.speed = float(data['speed'])
                    logging.info(f"set speed to: {self.speed}")

                if 'size' in data:
                    self.size = float(data['size'])
                    logging.info(f"set size to: {self.size}")

                if 'strength' in data:
                    self.strength = float(data['strength'])
                    logging.info(f"set str to: {self.strength}")
                
                if 'equalisation' in data:
                    self.equalisation = float(data['equalisation'])
                    logging.info(f"set equalisation to: {self.equalisation}")

                if 'mode' in data:
                    self.mode = data['mode']
                    logging.info(f"set mode to: {self.mode}")

                if 'hold' in data:
                    self.hold = bool(data['hold'])
                    logging.info(f"set hold to: {self.hold}")

                if 'max_speed' in data:
                    self.max_speed = float(data['max_speed'])
                    logging.info(f"set max_speed to: {self.max_speed}")

                if 'pressed' in data:
                    new = float(data['pressed'])
                    if self.pressed != new:
                        logging.info(f"set pressed to: {self.pressed}")
                    self.pressed = new

    def static(self, actuator:Actuator, value):
        actuator.set(value)
    
    def ripple(self, actuator:Actuator, center:Position, strength, speed):
        #create a ripple wave with the center position at its center
        dist = calc_dist(center, actuator.pos)
        ripple = self.calc_sin(dist, 0.75, speed)
        actuator.set(ripple * strength)

    def touch(self, actuator:Actuator, center:Position, strength, size):
        #increases or decreases the area around the touch center
        dist = calc_dist(center, actuator.pos)
        actuator.set(strength * size / dist)

    def calc_sin(self, dist, frequency, speed):
        val = time.time() * speed + dist*frequency
        rads = val * math.pi
        return (math.sin(rads) + 1) * 0.5
        

    def recalculate_actuators(self):
        for actuator in self.actuators:
            if self.pressed:
                match self.mode:
                    case "static":
                        self.static(actuator, abs(self.cursor.y))

                    case "push":
                        self.touch(actuator, self.cursor, self.strength*-1, self.size)

                    case "pull":
                        self.touch(actuator, self.cursor, self.strength, self.size)

                    case "ripple":
                        self.ripple(actuator, self.cursor, self.strength, self.speed)
            else:
                if not self.hold:
                    #release
                    self.static(actuator, self.volume)

    def equalize_actuators(self, desiredVolume:float):
        # adjusts all the actuators by a small amount to keep the volume consistent
        numActuators = 0.0
        totalDesiredVolume = 0.0
        totalActualVolume = 0.0

        for actuator in self.actuators:
            totalActualVolume += actuator.actuation
            totalDesiredVolume += desiredVolume
            numActuators += 1

        requiredChange = totalDesiredVolume - totalActualVolume
        requiredChangePerActuator = requiredChange / numActuators
        
        totalAfterVolume = 0
        for actuator in self.actuators:
            actuator.change(requiredChangePerActuator)
            totalAfterVolume += actuator.actuation
        #logging.info(f"Current colume: {totalAfterVolume:.2f}, desired volume: {totalDesiredVolume:.2f}")

    def send_to_client(self):
        data = []
        for actuator in self.actuators:
            data.append(actuator.to_dictionary())
        print(json.dumps(data), file=sys.stdout, flush=True)

    def send_to_actuators(self):
        for arduino in self.arduinos:
            data = []
            for actuator in arduino.actuators:
                data.append((actuator.pin, actuator.actuation))
            arduino.write(data)
            #logging.info(f"{arduino.UID} - {arduino.address} : {data}")

def main():
    controller = Controller()
    controller.load_config('config.csv')
    while True:
        try:
            time.sleep(iteration_delay)
            controller.calc_iteration_duration()
            controller.read_data()
            controller.recalculate_actuators()
            controller.equalize_actuators(controller.volume)
            controller.send_to_actuators()
            controller.send_to_client()
        except Exception as e:
            logging.info(f"Error: {e}")

if __name__ == "__main__":
    main()
