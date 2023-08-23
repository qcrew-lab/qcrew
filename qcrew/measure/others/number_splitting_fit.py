"""
V2
12 May 2023
Author: Kai Xiang
Email: kaixiang.lee19@sps.nus.edu.sg

================
Code to perform numerical curve-fitting on Lorentzian peaks of circuit QED measurements. Note that the
measurements gives the amplitude of a signal, and so the data has to be squared in order to use a 
Lorentzian fit. Also note that the number-splitting data distribution does not strictly follow a Lorentzian 
distribution, and so a simulation would be better

Dependencies: numpy, matplotlib, scipy, h5py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import h5py
import warnings

# Read File path
data_file_path = (
    r"C:\Users\qcrew\Desktop\qcrew\data\somerset\20230817\211619_somerset_qubit_spec.h5"
)

# Measurement average
data_key = "Z_AVG"

# Number of peaks
num_peaks = 4

# Initial Parameter Guesses
y_offset = 1- 4e-5

peak1 = {"Frequency": -36.50e6, "FWHM": 0.5e6, "Height": 8e-5}
peak2 = {"Frequency": -42e6, "FWHM": 0.5e6, "Height": 2e-5}
peak3 = {"Frequency": -46e6, "FWHM": 0.5e6, "Height": 0.5e-5}
peak4 = {"Frequency": -51e6, "FWHM": 0.5e6, "Height": 0.1e-5}
# peak5 = {"Frequency": 58e6, "FWHM": 0.1e6, "Height": 1e4}

params = [
    y_offset,
    peak1,
    peak2,
    peak3,
    peak4,
]


# ===================================================== #
f = h5py.File(data_file_path, "r")
data = f["data"][data_key]
data = np.array(data)

# Flip the peaks upright
min_val = np.min(data)
max_val = np.max(data)
med_val = np.median(data)

if np.abs(med_val - max_val) < np.abs(med_val - min_val):
    """Check if the median is closer to the top or the botton"""
    data *= -1

# Push the data above zero
data += 1

x_values = f["data"]["x"]
x_values = np.array(x_values)

# Lorentzian fit function
def Lorentzian(x, x0, gamma, I):
    """
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
    """

    intensity = I * (gamma ** 2) / ((x - x0) ** 2 + gamma ** 2)

    return intensity


# Multiple peak function
def fit_func(x, *args):
    """
    Combines several peaks into a single function to fit
    """
    global data, num_peaks

    total_function = np.zeros(x.shape, dtype="float")
    offset = args[0]

    for i in range(num_peaks):
        """Fit each peak"""
        params = args[1:][i * 3 : i * 3 + 3]
        params = [
            *params,
        ]
        total_function += Lorentzian(x, *params)

    """Adds the constant offset to all peaks"""
    total_function += offset

    return total_function.astype("float")


#############################

# Fills in the missing parameters
if len(params) != num_peaks + 1:
    warnings.warn("Number of peaks do not match up with provided guesses")

    if type(params[0]) is not int or type(params[0]) is not float:
        """Provides a y-offest if not given"""
        params = [
            np.mean(data),
        ] + params

    if type(params[-1]) != dict and len(params) < num_peaks + 1:
        """Provides example peak if no peaks present"""
        peak_guess = {
            "Frequency": x_values[0],
            "FWHM": (x_values[-1] - x_values[0]) / 10,
            "Height": np.mean(data),
        }

        params = params + [
            peak_guess,
        ]

    if len(params) < num_peaks + 1:
        """Fills up missing peaks"""
        params = (
            params
            + [
                params[-1].copy(),
            ]
            * (num_peaks + 1 - len(params))
        )

    print("Filled up initial guesses, fitting may not be precise")

p0 = [
    params[0],
]

for i in range(1, 1 + num_peaks):
    p0 += [params[i]["Frequency"], params[i]["FWHM"], params[i]["Height"]]

opt_params, cov = params, None

try:
    opt_params, cov = curve_fit(
        fit_func,
        x_values,
        data,
        p0=p0,
        maxfev=10_000,
    )
except:
    print("No solution found")

fitted_vals = [fit_func(x, *opt_params) for x in x_values]

# Print Optimal Parameters
print(f"Constant Signal Offset: {opt_params[0]}")
for i in range(num_peaks):
    freq = opt_params[i * 3 + 1]
    print()
    print(f"Peak {i + 1}")
    print(f"Centre Frequency: {freq/1e6} MHz")
    print(f"FWHM: {opt_params[i*3 + 2]/1e6} MHz")
    print(f"Fit Height: {opt_params[i*3 + 3]}")

    print(f"Peak Height from Offset: {fit_func(freq, *opt_params) - opt_params[0]}")

# Plot the fit
plt.plot(x_values, data, "b.")
plt.plot(x_values, fitted_vals, "r-")
plt.xlabel("Intermediate Frequency (Hz)")
plt.show()
