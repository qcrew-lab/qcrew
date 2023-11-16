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


cal_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231019/172001_somerset_characteristic_function_1D.h5"
data_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231019/174656_somerset_characteristic_function_2D.h5"

contrasts_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231019/173008_somerset_characteristic_function_1D.h5"

threshold = -0.0002898168253436553

# Get offset and amplitude from 1D vacuum data
file = h5py.File(cal_filename, "r")
data = file["data"]
state_correction = np.array(data["state"])
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
plt.title(f"1D Characteristic for amplitude and offset correction")
plt.legend()
plt.show()

# Get high-average contrasts for each state
file = h5py.File(contrasts_filename, "r")
data = file["data"]
states_contrast = np.array(data["state"])
contrast_0 = np.max((states_contrast[:, 0] - ofs) / amp)
contrast_1 = np.max((states_contrast[:, 1] - ofs) / amp)
contrast_2 = np.max((states_contrast[:, 2] - ofs) / amp)
print(contrast_1 / contrast_0, contrast_2 / contrast_0)

file = h5py.File(data_filename, "r")
data = file["data"]
state = (np.array(data["I"]) < threshold).astype(int)
state = state.flatten()  # revert the buffering of qcore
file.close()

# separate internal loop into even (0.0) and odd (0.5) and state
vacuum_real = state[::6]
vacuum_imag = state[1::6]
fock1_real = state[2::6]
fock1_imag = state[3::6]
fock2_real = state[4::6]
fock2_imag = state[5::6]

# Get x and y sweeps for buffering and plotting
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
y = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)

reps = len(vacuum_real) // (len(y) * len(x))
buffer = (reps, len(y), len(x))

vacuum_real_avg = np.average(np.reshape(vacuum_real, buffer), axis=0)
vacuum_imag_avg = np.average(np.reshape(vacuum_imag, buffer), axis=0)
fock1_real_avg = np.average(np.reshape(fock1_real, buffer), axis=0)
fock1_imag_avg = np.average(np.reshape(fock1_imag, buffer), axis=0)
fock2_real_avg = np.average(np.reshape(fock2_real, buffer), axis=0)
fock2_imag_avg = np.average(np.reshape(fock2_imag, buffer), axis=0)

ofs = np.average(vacuum_imag_avg)  # second estimate of offset
vacuum_real_cor = correct_ofs_and_amp(reshape_and_avg(vacuum_real, buffer), amp, ofs)
vacuum_imag_cor = correct_ofs_and_amp(reshape_and_avg(vacuum_imag, buffer), amp, ofs)
fock1_real_cor = correct_ofs_and_amp(reshape_and_avg(fock1_real, buffer), amp, ofs)
fock1_imag_cor = correct_ofs_and_amp(reshape_and_avg(fock1_imag, buffer), amp, ofs)
fock2_real_cor = correct_ofs_and_amp(reshape_and_avg(fock2_real, buffer), amp, ofs)
fock2_imag_cor = correct_ofs_and_amp(reshape_and_avg(fock2_imag, buffer), amp, ofs)

print(ofs, amp)

# Final Fock 0, 1, 2 wigner plots
fig, ax = plt.subplots(2, 3)

im = ax[0, 0].pcolormesh(
    x, y, vacuum_real_cor, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[1, 0].pcolormesh(
    x, y, vacuum_imag_cor, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[0, 1].pcolormesh(
    x, y, fock1_real_cor, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[1, 1].pcolormesh(
    x, y, fock1_imag_cor, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[0, 2].pcolormesh(
    x, y, fock2_real_cor, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[1, 2].pcolormesh(
    x, y, fock2_imag_cor, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
ax[0, 0].set_title(
    f"max = {np.max(vacuum_real_cor):.3f}\nmin = {np.min(vacuum_real_cor):.3f}"
)
ax[0, 1].set_title(
    f"max = {np.max(fock1_real_cor):.3f}\nmin = {np.min(fock1_real_cor):.3f}"
)
ax[0, 2].set_title(
    f"max = {np.max(fock2_real_cor):.3f}\nmin = {np.min(fock2_real_cor):.3f}"
)

ax[0, 0].set_aspect("equal", "box")
ax[0, 1].set_aspect("equal", "box")
ax[0, 2].set_aspect("equal", "box")
ax[1, 0].set_aspect("equal", "box")
ax[1, 1].set_aspect("equal", "box")
ax[1, 2].set_aspect("equal", "box")

fig.tight_layout()

plt.legend()
plt.show()
