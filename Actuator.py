
max_speed = 0.2

import time

from common import Position, clamp

iteration_duration = 0.05
last_iteration = time.time()


class Actuator:
    def __init__(self, arduino, pin, pos: Position):
        #print("new actuator:", arduino, pin, x, y, file=sys.stderr)
        self.arduino = arduino # UID of the arduino
        self.pin = pin # pin number the actuator is connected to on the arduino
        self.pos = pos # holds x and y position
        self.actuation = 0.5

        #prevents overshooting/oscillating servos
        self.deadzone = 0.01

    def get_pos(self):
        return self.pos
    
    def get_max_change(self):
        #return iteration_duration * self.max_speed
        return 0.05

    def set(self, new:float):
        diff = new - self.actuation
        self.change(diff)

    def change(self, change:float):
        # move the actuation closer to the desired
        if (abs(change) < self.deadzone): return
        max_chance = self.get_max_change()
        true_change = clamp(-max_chance, max_chance, change)
        self.actuation = self.actuation + true_change

    def to_dictionary(self):
        return {"actuation": clamp(0, 1, self.actuation),
                'x': self.pos.x, 
                'y': self.pos.y, 
                'pin': self.pin,
                'arduino': self.arduino}