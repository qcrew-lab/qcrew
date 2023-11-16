from random import gauss
from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit


def gaussian(x, a, b, sigma, c):
    return a * np.exp(-((x - b) ** 2) / (2 * sigma ** 2)) + c


def linear(x, a, b):
    return a * x + b


def gaussian_fit(x, y, bounds, guess):
    # mean_arg = np.argmax(y)
    # mean = x[mean_arg]
    # fit_range = int(1 * len(x))
    # x_sample = x[mean_arg - fit_range : mean_arg + fit_range]
    # y_sample = y[mean_arg - fit_range : mean_arg + fit_range]
    popt, pcov = curve_fit(
        gaussian,
        x,
        y,
        bounds=bounds, 
        p0=guess,
    )
    return popt


def linear_fit(x, y):
    mean_arg = np.argmax(y)
    mean = x[mean_arg]
    x_sample = x
    y_sample = y
    popt, pcov = curve_fit(
        linear,
        x_sample,
        y_sample,
        bounds=(
            (-2 / 300, 0.0),
            (2 / 300, 1.0),
        ),
        p0=[0.2 / 300, 0.5],
    )
    return popt


filename_A = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231018/140356_somerset_out_and_back.h5"
filename_B = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231018/134304_somerset_out_and_back.h5"

file = h5py.File(filename_A, "r")
data = file["data"]
state1 = np.array(data["I_AVG"])  # data["PHASE"]
y1 = np.array(data["y"])  # data["PHASE"]
x1 = np.array(data["x"])
file.close()

file = h5py.File(filename_B, "r")
data = file["data"]
state2 = np.array(data["I_AVG"])  # data["PHASE"]
y2 = np.array(data["y"])  # data["PHASE"]
x2 = np.array(data["x"])
file.close()


fig, ax = plt.subplots(2, 2)
fit_maximum_A = []
for i in range(state1.shape[0]):

    bounds = [(0.00, 0.5, 0.0, -np.inf), (0.0010, 0.8, 0.5, np.inf)]
    guess = [0.0005, 0.7, 0.25, 0]

    ax[0, 0].plot(y1[i, 22:], state1[i, 22:])
    y_fit = y1[i, 22:]
    state_fit = state1[i, 22:]
    popt = gaussian_fit(y_fit, state_fit, bounds, guess)
    fit_maximum_A.append(popt[1])

ax[1, 0].scatter(x1[:, 0], fit_maximum_A)
popt = linear_fit(x1[:, 0], fit_maximum_A)
ax[1, 0].plot(x1[:, 0], linear(x1[:, 0], *popt), label=popt)
ax[1, 0].legend()


fit_maximum_B = []
for i in range(state2.shape[0]):

    bounds = [(0, 0.0, 0.0, -np.inf), (0.001, 0.5, 0.3, np.inf)]
    guess = [0.0003, 0.35, 0.25, 0]

    ax[0, 1].plot(y2[i, : y2.shape[1] // 2], state2[i, : y2.shape[1] // 2])
    popt = gaussian_fit(y2[i, :], state2[i, :], bounds, guess)
    # ax[0, 1].plot(y2[i, :], gaussian(y2[i, :], *popt))
    fit_maximum_B.append(popt[1])

ax[1, 1].scatter(x2[:, 0], fit_maximum_B)
popt = linear_fit(x2[:, 0], fit_maximum_B)
# print(linear(x2[i, :], *popt).shape, x2[i, :].shape)
ax[1, 1].plot(x2[:, 0], linear(x2[:, 0], *popt), label=popt)

# ax.pcolormesh(x1, y1, state1)

plt.legend()

plt.show()
