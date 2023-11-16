from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit


filepath_list = [
    # "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231011/194309_somerset_characteristic_function_2D.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231013/170704_somerset_wigner_1d.h5",
]

file = h5py.File(filepath_list[0], "r")
data = file["data"]
state1 = np.array(data["state"][:, 0])
# state2 = np.array(data["state"][:, 1])  # data["PHASE"]
# state1 = np.average(state1[:5000, :], axis=0)
# y1 = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
x1 = np.array(data["x"][:, 0])  # np.array(data["internal sweep"])
# print(len(y1), len(x1))
# state1 = np.reshape(state1, (len(x1), len(y1)))
# threshold =

fig, ax = plt.subplots()
im = ax.scatter(
    x1,
    state1,
)


def gaussian(x, a, b, sigma, c):
    return a * np.exp(-((x - b) ** 2) / (2 * sigma ** 2)) + c


def gaussian_fit(x, y):
    mean_arg = np.argmax(y)
    mean = x[mean_arg]
    # fit_range = int(0.2 * len(x))
    x_sample = x  # [mean_arg - fit_range : mean_arg + fit_range]
    y_sample = y  # [mean_arg - fit_range : mean_arg + fit_range]
    popt, pcov = curve_fit(
        gaussian,
        x_sample,
        y_sample,
        bounds=(
            (0, min(x_sample), -np.inf, -np.inf),
            (np.inf, max(x_sample), np.inf, np.inf),
        ),
        p0=[max(y) - min(y), 0, 0.5, min(y)],
    )
    return popt


popt = gaussian_fit(x1, state1)
y_fit = gaussian(x1, *popt)
ax.plot(
    x1,
    y_fit,
)
print(popt)

plt.show()
