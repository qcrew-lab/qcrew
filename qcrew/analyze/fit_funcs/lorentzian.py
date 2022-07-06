import numpy as np

def func(xs, area=10, x0=0, w=2):
    '''
    Lorentzian defined by it's area <area>, width <w>, position <x0> and
    y-offset <ofs>.
    '''
    return 2 * area * w / np.pi / (4 * (xs - x0)**2 + w**2)

def guess(xs, ys):
    #yofs = (ys[0] + ys[-1]) / 2
    #ys = ys - yofs
    maxidx = np.argmax(np.abs(ys))
    area = np.sum(ys)
    w = (xs[-1] - xs[0]) / 5
    return dict(
        area=area,
        x0=xs[maxidx],
        w=w,
    )
