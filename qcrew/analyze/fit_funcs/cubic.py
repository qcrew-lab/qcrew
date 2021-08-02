import numpy as np

def func(xs, a=1, b=1, c=1, d=1):
    return a * xs**3 + b * xs**2 + c*xs + d

def guess(xs, ys):
    p = np.polyfit(xs, ys, 3)
    return dict(a=p[0], b=p[1], c=p[2], d=p[3])

