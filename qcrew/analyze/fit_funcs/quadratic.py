import numpy as np

def func(xs, a=1, b=1, c=0):
    return a * xs**2 + b * xs + c

def guess(xs, ys):
    p = np.polyfit(xs, ys, 2)
    return dict(a=p[0], b=p[1], c=p[2])

