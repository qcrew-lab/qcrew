import numpy as np

def func(xs, a=1, b=1):
    return a * xs + b

def guess(xs, ys):
    p = np.polyfit(xs, ys, 1)
    return dict(a=p[0], b=p[1])

