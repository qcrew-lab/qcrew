from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit

# filepath_list_A = [
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/203918_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/212703_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/214145_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/223600_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/224956_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/233330_somerset_wigner_2d.h5",
# ]
# filepath_list_B = [
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/205818_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/211309_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/220621_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/222135_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/230337_somerset_wigner_2d.h5",
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231010/231827_somerset_wigner_2d.h5",
# ]
filepath_list_A = [
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231011/010047_somerset_wigner_2d.h5",
]
filepath_list_B = [
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231011/004701_somerset_wigner_2d.h5",
]
state1 = []
for filepath in filepath_list_A:
    file = h5py.File(filepath, "r")
    data = file["data"]
    state1.append(data["state"])  # data["PHASE"]
    y1 = data["y"]  # data["PHASE"]
    x1 = data["x"]
state1 = np.average(np.array(state1), axis=0)


state2 = []
for filepath in filepath_list_B:
    file = h5py.File(filepath, "r")
    data = file["data"]
    state2.append(data["state"])  # data["PHASE"]
    y2 = data["y"]  # data["PHASE"]
    x2 = data["x"]
state2 = np.average(np.array(state2), axis=0)

parity = np.array(state2) - np.array(state1)

max_amp = 4.69719926e-01
offset = -4.15005610e-02

parity /= max_amp
# def gaussian(x, a, b, sigma, c):
#     return a * np.exp(-((x - b) ** 2) / (2 * sigma ** 2)) + c


# def gaussian_fit(x, y):
#     mean_arg = np.argmax(y)
#     mean = x[mean_arg]
#     fit_range = int(0.2 * len(x))
#     x_sample = x[mean_arg - fit_range : mean_arg + fit_range]
#     y_sample = y[mean_arg - fit_range : mean_arg + fit_range]
#     popt, pcov = curve_fit(
#         gaussian,
#         x_sample,
#         y_sample,
#         bounds=(
#             (0, min(x_sample), -np.inf, -np.inf),
#             (np.inf, max(x_sample), np.inf, np.inf),
#         ),
#         p0=[1, 0, 0.5, 0],
#     )
#     return popt
# popt = gaussian_fit(np.array(x[:, 0]), y_sub)
# y_fit = gaussian(np.array(x[:, 0]), *popt)
print(np.min(parity), np.sum(parity))
fig, ax = plt.subplots()
im = ax.pcolormesh(
    x1,
    y1,
    parity,
    norm=colors.Normalize(vmin=-1, vmax=1),
    shading="auto",
    cmap="bwr",
)

cbar = fig.colorbar(im)
cbar.set_ticks([np.min(parity), np.max(parity)])
# im.set_clim(vmin=np.min(parity), vmax=np.max(parity))
# Set plot parameters
# ax.set_ylabel(self.plot_setup["ylabel"])
# cbar.set_label(self.plot_setup["zlabel"])

# y_sub = np.array(y[:, 0]) - np.array(y[:, 1])
# popt = gaussian_fit(np.array(x[:, 0]), y_sub)
# print(popt)
# y_fit = gaussian(np.array(x[:, 0]), *popt)
# plt.scatter(np.array(x[:, 0]), np.array(y[:, 0]) - np.array(y[:, 1]))
# plt.plot(np.array(x[:, 0]), y_fit)

plt.legend()
plt.ylabel("Im")  # phase
plt.xlabel("Re")  # . Qubit LO = 1.4 GHz")
# plt.show()

from qutip import basis, wigner

n = 1
fock_state = basis(2, n)  # Creating a Fock state with 2 energy levels (qubit)

x = np.linspace(-3, 3, 200)  # Define the range of x values for the Wigner function
p = np.linspace(-3, 3, 200)  # Define the range of p values for the Wigner function
W = wigner(fock_state, x, p)
print(np.max(W), np.min(W))
# W /= np.max(W)

# im = ax[1].pcolormesh(
#     x,
#     p,
#     W,
#     norm=colors.Normalize(vmin=-1, vmax=1),
#     shading="auto",
#     cmap="bwr",
# )

plt.show()
