from random import gauss
from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit


def gaussian(xs, x0, sig, amp, ofs):
    return ofs + amp * np.exp(-(xs - x0)**2 / (2 * sig**2))

def guess_to_gaussian(xs, ys): #xy
    ofs = (ys[0] + ys[-1]) / 2
    peak_idx = np.argmax(abs(ys - ofs))
    x0 = xs[peak_idx]
    sig = abs(xs[-1] - xs[0]) / 10
    amp = ys[peak_idx] - ofs
    yrange = np.max(ys) - np.min(ys)
    p0_mean=x0
    p0_std=sig
    p0_amp=amp
    p0_off=ofs
    p0 = [p0_mean, p0_std, p0_amp, p0_off]
    return p0

## load data
filename_A = "C:/Users/qcrew/Documents/fast-flux-line/fast-flux-line/pulse_predistortion/20231114_223315_pi_pulse_scope_cut.h5"

file = h5py.File(filename_A, "r")
state1 = np.array(file["data"])  # state # add minus sign may fit better if feature is a dip
y1 = np.array(file["y"])  # phase
x1 = np.array(file["x"]) #delay time
file.close()

plt.pcolormesh(x1, y1, state1)
plt.colorbar()
plt.show()

# fit all data
# fit guassian
fit_maximum_A = []
for i in range(state1.shape[1]): #delay time state1.shape[0]
    
    xs = x1[:, i]
    ys = state1[:, i]
    if 0: #no plot
        plt.plot(xs, ys, label = "data")    
    p0 = guess_to_gaussian(xs, ys)
    # print("p0_mean, p0_std, p0_amp, p0_off", p0[0], p0[1], p0[2], p0[3])
    popt, pcov = curve_fit(gaussian, xs, ys, p0=p0, maxfev=1000000000) # bounds=bounds
    if 0:
        plt.plot(xs, [gaussian(f, popt[0], popt[1], popt[2], popt[3]) for f in xs], label = "fit")
        plt.legend()
        plt.show()
    fit_maximum_A.append(popt[0])
    
plt.plot(-y1[1, :], fit_maximum_A,"-." , label='fit', color='blue')
plt.show()