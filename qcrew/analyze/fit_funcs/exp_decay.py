import numpy as np

def func(xs, A=1, tau=1, ofs=0):
    return A * np.exp(-xs / tau)+ofs
def guess(xs, ys):
    yofs = ys[-1]
    ys = ys - yofs
    tau = (xs[-1] - xs[0]) / 5
    return dict(
        A=ys[0],
        tau=(tau, 0, 100*tau),
        ofs=yofs,
    )

TEST_RANGE = 0, 100
TEST_PARAMS = dict(A=-5, tau=10)
