from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit


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


data_filename = (
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231017/121026_somerset_wigner_2d.h5"
)

threshold = -0.00014472961900504353

### Get amplitude and offset
# file = h5py.File(data_filename, "r")
# data = file["data"]
# state_correction_A = np.array(data["state"][:, 0])
# state_correction_B = np.array(data["state"][:, 1])
# state_correction = state_correction_A - state_correction_B
# x = np.array(data["x"][:, 0])
# file.close()
# fig, ax = plt.subplots()
# im = ax.scatter(x, state_correction, label="data")
# popt = gaussian_fit(x, state_correction)
# y_fit = gaussian(x, *popt)
# amp = popt[0]
# sig = popt[2]
# ofs = popt[3]
# ax.plot(x, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")

# plt.title(f"1D Wigner for amplitude and offset correction #{i}")
# plt.legend()

file = h5py.File(data_filename, "r")
data = file["data"]
print(np.array(data["x"]))
state = (np.array(data["I"]) < threshold).astype(int)
state = state.flatten()  # revert the buffering of qcore

# separate internal loop into even (0.0) and odd (0.5) and state
even_vacuum = state[::4]
odd_vacuum = state[1::4]
even_fock1 = state[2::4]
odd_fock1 = state[3::4]

# Get x and y sweeps for buffering and plotting
y = np.arange(0.13, 0.15 + 0.002 / 2, 0.002)
x = np.arange(23, 33, 1)

# reps for buffering and averaging
reps = len(even_vacuum) // (len(y) * len(x))
buffer = (reps, len(y), len(x))
print(buffer)
print(even_vacuum.shape)
even_vacuum_avg = np.average(np.reshape(even_vacuum, buffer), axis=0)
odd_vacuum_avg = np.average(np.reshape(odd_vacuum, buffer), axis=0)
even_fock1_avg = np.average(np.reshape(even_fock1, buffer), axis=0)
odd_fock1_avg = np.average(np.reshape(odd_fock1, buffer), axis=0)

print(even_vacuum_avg.shape)
fig, ax = plt.subplots()

offset_matrix = (even_vacuum_avg + odd_vacuum_avg) / 2
amplitude_matrix = even_vacuum_avg - odd_vacuum_avg

ofs = 0  # np.average(offset_matrix)
amp = np.average(amplitude_matrix)
print(ofs, amp)

fock1_avg = even_fock1_avg - odd_fock1_avg
fock1_corrected = (fock1_avg - ofs) / amp
print(np.max(fock1_avg), np.min(fock1_avg))
print(np.max(fock1_corrected), np.min(fock1_corrected))
ax.pcolormesh(x, y, fock1_avg)
plt.show()
ax.pcolormesh(x, y, fock1_avg)
plt.show()
