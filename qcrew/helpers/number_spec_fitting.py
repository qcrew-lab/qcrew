import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import h5py
from pathlib import Path

directory = 'C:/Users/qcrew/Desktop/qcrew/data/YABBAv4'

file = 'C:/Users/qcrew/Desktop/qcrew/data/YABBAv4/20230309/144808_YABBA_qubit_spec_number_split.h5'

f = h5py.File(file, 'r')
data = f['data']['Q_AVG'][:]

# Number of peaks
n = 5

# Initial guess of parameters
p0 = [
    -20e-6,
    -29.98e6, 1e6, -1e-5, 
    -30.57e6, 1e6, -1e-5, 
    -31.16e6, 1e6, -1e-5,
    -31.745e6, 1e6, -1e-5,
    -32.33e6, 1e6, -1e-5, 
    # -32.915e6, 1e6, -1e-6,
    ]

# X values
x_range = np.linspace(-35e6, -29e6, data.shape[0])

# Lorentzian fit function
def Lorentzian(x, x0, gamma, I, offset):
    '''
    A function describing a Lorentzian with three parameters

    Parameters
    --------------
    x : float/int
        Dependent variable

    x0: float/int
        Location parameter, represents the location of the peak

    gamma: float/int
        Scale parameter, represents the FWHM = 2*gamma

    I: float/int
        Peak height

    offset: float/int
        Offset from x-axis
    '''

    return I * (gamma**2) / ((x - x0)**2 + gamma**2) + offset

# Multiple peak function
def fit_func(x, *args):
    '''
    Combines several peaks into a single function to fit
    '''
    global n

    if len(args) != 3*n + 1:
        raise Exception("Wrong number of variables")

    total_function = np.zeros(x.shape, dtype = 'float')
    offset = args[0]

    for i in range(n):
        params = *args[i*3 + 1: i*3 + 4], offset
        total_function += Lorentzian(x, *params)

    return total_function.astype('float')

opt_params, cov = curve_fit(
    fit_func,
    x_range,
    data,
    p0 = p0,
    maxfev = 40_000,
    )

fitted_vals = [fit_func(x, *opt_params) for x in x_range]

plt.plot(x_range, data, 'b.')
plt.plot(x_range, fitted_vals, 'r-')
plt.show()

print(opt_params)
