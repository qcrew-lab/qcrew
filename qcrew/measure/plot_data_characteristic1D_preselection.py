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


# char1d_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231101/135238_somerset_characteristic_function_1D.h5"
char1d_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231116/000112_somerset_characteristic_function_1D_preselect_lk.h5"

threshold =  -0.00014579810270391258

# Get offset and amplitude from 1D vacuum data
file = h5py.File(char1d_filename, "r")
data = file["data"]
state = np.array((np.array(data["I"])) < threshold).astype(int)
file.close()


state = state.flatten()
m1 = state[::2]
m2 = state[1::2]
# plt.plot(np.average(np.reshape(m2, (-1, 78))[::2], axis=0))
# plt.plot(np.average(np.reshape(m2, (-1, 78))[1::2], axis=0))
# plt.show()

# Get x and y sweeps for buffering and plotting
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
y = ["Real", "Imag"]

reps = len(m2) // (len(y) * len(x))
buffer = (reps, len(x), len(y))

# select_mask = np.where(m1 == 0)  # first_selection

select_data = np.where(m1 == 0, m2, np.nan)  # first_selection
print(m1[:10])
print(m2[:10])
print(select_data[:10])
select_data_rate = np.average(np.where(m1 == 0, 1, 0))  # first_selection
print("Preselection rate: ", select_data_rate)

select_data = np.reshape(select_data, buffer)
m2 = np.reshape(m2, buffer)
select_data = np.nanmean(select_data, axis=0)
m2 = np.nanmean(m2, axis=0)
print(select_data.shape)
select_data_real = select_data[:, 0]
select_data_imag = select_data[:, 1]

# state_correction = np.average(state_correction, axis=0)
fig, ax = plt.subplots(1, 2, sharey=True)
im = ax[0].scatter(x, m2[:, 0], label="data real")
im = ax[0].scatter(x, m2[:, 1], label="data imag")
popt = gaussian_fit(x, m2[:, 0])
y_fit = gaussian(x, *popt)
amp = popt[0]
sig = popt[2]
ofs = popt[3]
ax[0].set_title("without preselection")
ax[0].plot(x, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")

im = ax[1].scatter(x, select_data_real, label="")
im = ax[1].scatter(x, select_data_imag, label="with preselection")
popt = gaussian_fit(x, select_data_real)
y_fit = gaussian(x, *popt)
amp = popt[0]
sig = popt[2]
ofs = popt[3]
ax[1].plot(x, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")
ax[1].set_title(f"with preselection ({select_data_rate*100:.1f}%)")
ax[0].legend()
ax[0].grid()
ax[1].legend()
ax[1].grid()
plt.show()
