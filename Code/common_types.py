from collections import namedtuple

Coordinates = namedtuple('Coordinates', ['x', 'y'])
Coordinates.__doc__ = "Representation of a coordinate in a cartesian plane."
Coordinates.x.__doc__ = 'The distance from the origin on the X axis.'
Coordinates.y.__doc__ = 'The distance from the origin on the Y axis.'


def distance(a, b):
    """Calculates the L1 distance between the two given coordinates."""
    return abs(a.x - b.x) + abs(a.y - b.y)
