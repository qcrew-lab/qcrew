from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit


filepath_list = [
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/113157_somerset_wigner_2d.h5",
]

threshold = -0.00016580276302722175
file = h5py.File(filepath_list[0], "r")
data = file["data"]
state = np.array(data["I"])  # < threshold
state = state.flatten()  # revert the buffering of qcore
# separate internal loop into even (0.0) and odd (0.5)
even_state1 = state[::2]
odd_state1 = state[1::2]
# Get x and y sweeps for buffering and plotting
y = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
# reps for buffering and averaging
reps = 102  # len(even_state)//(len(y)*len(x))
buffer = (reps, len(y), len(x))
even_state1_avg = np.average(np.reshape(even_state1, buffer), axis=0)
odd_state1_avg = np.average(np.reshape(odd_state1, buffer), axis=0)
print(even_state1_avg.shape)

fig, ax = plt.subplots(1, 2)
im = ax[0].pcolormesh(
    x,
    y,
    even_state1_avg,
    # norm=colors.Normalize(vmin=-1, vmax=1),
    cmap="bwr",
)
im = ax[1].pcolormesh(
    x,
    y,
    odd_state1_avg,
    # norm=colors.Normalize(vmin=-1, vmax=1),
    cmap="bwr",
)


plt.show()
