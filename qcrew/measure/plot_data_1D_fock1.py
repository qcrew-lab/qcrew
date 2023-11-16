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
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231017/112351_somerset_wigner_1d.h5"
)

threshold = -0.00014472961900504353

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
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)

# reps for buffering and averaging
reps = len(even_vacuum) // len(x)
buffer = (reps, len(x))
print(buffer)
print(even_vacuum.shape)
even_vacuum_avg = np.average(np.reshape(even_vacuum, buffer), axis=0)
odd_vacuum_avg = np.average(np.reshape(odd_vacuum, buffer), axis=0)
even_fock1_avg = np.average(np.reshape(even_fock1, buffer), axis=0)
odd_fock1_avg = np.average(np.reshape(odd_fock1, buffer), axis=0)

### Get amplitude and offset
vacuum_avg = even_vacuum_avg - odd_vacuum_avg
fig, ax = plt.subplots()
im = ax.scatter(x, vacuum_avg, label="data")
popt = gaussian_fit(x, vacuum_avg)
y_fit = gaussian(x, *popt)
amp = popt[0]
sig = popt[2]
ofs = popt[3]
ax.plot(x, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")
plt.title(f"Vacuum Wigner for amplitude and offset correction")
plt.legend()
plt.show()

fig, ax = plt.subplots()

fock1_avg = even_fock1_avg - odd_fock1_avg
fock1_corrected = (fock1_avg - ofs) / amp
ax.scatter(x, fock1_corrected)
plt.title(f"Corrected Wigner of Fock state 1")
plt.grid()
plt.show()
