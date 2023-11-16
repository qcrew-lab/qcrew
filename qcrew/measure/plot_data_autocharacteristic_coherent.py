from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit


def reshape_and_avg(data_array, buffer):
    return np.average(np.reshape(data_array, buffer), axis=0)


def correct_ofs_and_amp(data_array, amp, ofs):
    return (data_array - ofs) / amp


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
            (-np.inf, min(x_sample), -np.inf, -np.inf),
            (np.inf, max(x_sample), np.inf, np.inf),
        ),
        p0=[max(y) - min(y), 0, 0.5, max(y)],
    )
    return popt


cal_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231031/184730_somerset_characteristic_function_1D.h5"
data_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231031/230941_somerset_characteristic_function_2D.h5"

threshold = -0.00010421252794480583

# Get offset and amplitude from 1D vacuum data
file = h5py.File(cal_filename, "r")
data = file["data"]
state_correction = np.array(data["state"])[:, 0]
# ((np.array(data["I"])) < threshold).astype(int)
# state_correction = np.average(state_correction, axis=0)
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
file.close()
fig, ax = plt.subplots()
im = ax.scatter(x, state_correction, label="data")
popt = gaussian_fit(x, state_correction)
y_fit = gaussian(x, *popt)
amp = popt[0]
sig = popt[2]
ofs = popt[3]
ax.plot(x, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")
plt.title(f"1D Vacuum characteristic for amplitude and offset correction")
plt.legend()
plt.show()

# Get data and apply threshold
file = h5py.File(data_filename, "r")
data = file["data"]
state = (np.array(data["I"]) < threshold).astype(int)
state = state.flatten()  # revert the buffering of qcore
file.close()

# separate internal loop into even (0.0) and odd (0.5) and state
cohstate1_imag = state[0::5]
cohstate2_imag = state[1::5]
cohstate3_imag = state[2::5]
cohstate4_imag = state[3::5]
cohstate5_imag = state[4::5]

# Get x and y sweeps for buffering and plotting
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1) / sig
y = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1) / sig

reps = len(cohstate4_imag) // (len(y) * len(x))
buffer = (reps, len(y), len(x))

cohstate1_imag = correct_ofs_and_amp(reshape_and_avg(cohstate1_imag, buffer), amp, ofs)
cohstate2_imag = correct_ofs_and_amp(reshape_and_avg(cohstate2_imag, buffer), amp, ofs)
cohstate3_imag = correct_ofs_and_amp(reshape_and_avg(cohstate3_imag, buffer), amp, ofs)
cohstate4_imag = correct_ofs_and_amp(reshape_and_avg(cohstate4_imag, buffer), amp, ofs)
cohstate5_imag = correct_ofs_and_amp(reshape_and_avg(cohstate5_imag, buffer), amp, ofs)


# Final Fock 0, 1, 2 wigner plots
fig, ax = plt.subplots(1, 5)
im = ax[0].pcolormesh(
    x, y, cohstate1_imag, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[1].pcolormesh(
    x, y, cohstate2_imag, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[2].pcolormesh(
    x, y, cohstate3_imag, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[3].pcolormesh(
    x, y, cohstate4_imag, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[4].pcolormesh(
    x, y, cohstate5_imag, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
ax[0].set_aspect("equal", "box")
ax[1].set_aspect("equal", "box")
ax[2].set_aspect("equal", "box")
ax[3].set_aspect("equal", "box")
ax[4].set_aspect("equal", "box")

ax[0].set_xticks([-2.0, 0.0, 2.0])
ax[1].set_xticks([-2.0, 0.0, 2.0])
ax[2].set_xticks([-2.0, 0.0, 2.0])
ax[3].set_xticks([-2.0, 0.0, 2.0])
ax[4].set_xticks([-2.0, 0.0, 2.0])

ax[0].set_yticks([-2.0, 0.0, 2.0])
ax[1].set_yticks([-2.0, 0.0, 2.0])
ax[2].set_yticks([-2.0, 0.0, 2.0])
ax[3].set_yticks([-2.0, 0.0, 2.0])
ax[4].set_yticks([-2.0, 0.0, 2.0])
fig.tight_layout()

# lt.legend()
plt.show()
