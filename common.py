from dataclasses import dataclass
import math

@dataclass
class Position:
    x: float
    y: float

def clamp(lower, upper, value):
    return min(upper, max(lower, value))

def calc_dist(point1:Position, point2:Position):
        #calculate the distance between point 1 and point 2
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    