from pygame.math import *

def counter(start=0, stop=None, step=1):
    '''Count from [start=0] to [stop=None]'''
    if not stop:
        while True:
            yield start
            start += step
    else:
        yield from range(start, stop, step)

def mix(a, b, pos=0.5):
    try:
        return a + pos * (b-a)
    except TypeError:
        return [xa + pos * (xb-xa) for xa, xb in zip(a, b)]

def round_to_int(x):
    i = int(x)
    return i if x - i < 0.5 else i + 1