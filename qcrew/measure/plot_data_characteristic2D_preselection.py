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


path = "C:/Users/qcrew/Desktop/qcrew/data/somerset/"
cal_filenames = [
    path + "20231116/000112_somerset_characteristic_function_1D_preselect_lk.h5",
    # path + "20231101/135238_somerset_characteristic_function_1D.h5",
    # path + "20231031/085807_somerset_characteristic_function_1D.h5",
    # path + "20231031/085807_somerset_characteristic_function_1D.h5",
]
char2d_filenames = [
    path + "20231116/003115_somerset_characteristic_function_2D_chi_preselect_lk.h5",
    # path + "20231101/152233_somerset_characteristic_function_2D.h5",
    # path + "20231031/094158_somerset_characteristic_function_2D.h5",
]

threshold = -0.00014579810270391258
final_data = []
total_reps = 0

for i in range(len(cal_filenames)):
    cal_filename = cal_filenames[i]
    char2d_filename = char2d_filenames[i]

    # Get offset and amplitude from 1D vacuum data
    file = h5py.File(cal_filename, "r")
    data = file["data"]
    state_cal = np.array((np.array(data["I"])) < threshold).astype(int)
    file.close()

    state_cal = state_cal.flatten()
    m1_cal = state_cal[::2]
    m2_cal = state_cal[1::2]

    # Get x and y sweeps for buffering and plotting
    x_cal = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
    y_cal = ["Real", "Imag"]

    reps_cal = len(m2_cal) // (len(y_cal) * len(x_cal))
    buffer_cal = (reps_cal, len(x_cal), len(y_cal))

    select_cal_data = np.where(m1_cal == 0, m2_cal, np.nan)
    select_data_rate = np.average(np.where(m1_cal == 0, 1, 0))  # first_selection

    select_cal_data = np.reshape(select_cal_data, buffer_cal)
    select_cal_data = np.nanmean(select_cal_data, axis=0)
    m2_cal = np.reshape(m2_cal, buffer_cal)
    m2_cal = np.nanmean(m2_cal, axis=0)
    print(select_cal_data.shape)
    select_cal_data_real = select_cal_data[:, 0]
    select_cal_data_imag = select_cal_data[:, 1]

    fig, ax = plt.subplots(1, 2, sharey=True)
    im = ax[0].scatter(x_cal, m2_cal[:, 0], label="data real")
    im = ax[0].scatter(x_cal, m2_cal[:, 1], label="data imag")
    popt = gaussian_fit(x_cal, m2_cal[:, 0])
    y_fit = gaussian(x_cal, *popt)
    ax[0].set_title("without preselection")
    ax[0].plot(
        x_cal,
        y_fit,
        label=f"amp = {popt[0]:.3f}\nsig = {popt[2]:.3f}\nofs = {popt[3]:.3f}",
    )

    im = ax[1].scatter(x_cal, select_cal_data_real, label="")
    im = ax[1].scatter(x_cal, select_cal_data_imag, label="with preselection")
    popt = gaussian_fit(x_cal, select_cal_data_real)
    y_fit = gaussian(x_cal, *popt)
    amp = popt[0]
    sig = popt[2]
    ofs = popt[3]
    ax[1].plot(x_cal, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")
    ax[1].set_title(f"with preselection ({select_data_rate*100:.1f}% x {reps_cal:d})")
    ax[0].legend()
    ax[0].grid()
    ax[1].legend()
    ax[1].grid()
    fig.suptitle(f"Calibration #{i}")
    plt.show()

    # Get offset and amplitude from 1D vacuum data
    file = h5py.File(char2d_filename, "r")
    data = file["data"]
    state = np.array((np.array(data["I"])) < threshold).astype(int)
    file.close()
    state = state.flatten()
    m1 = state[::2]
    m2 = state[1::2]

    # Get x and y sweeps for buffering and plotting
    x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1) / sig
    y = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1) / sig

    reps = len(m2) // (len(y) * len(x))
    total_reps += reps
    print(reps)
    buffer = (reps, len(x), len(y))

    select_data = np.where(m1 == 0, m2, np.nan)  # first_selection
    select_data_rate = np.average(np.where(m1 == 0, 1, 0))  # first_selection

    print(select_data.shape)
    select_data = np.reshape(select_data, buffer)
    select_data = correct_ofs_and_amp(select_data, amp, ofs)
    final_data.append(select_data)
    m2 = np.reshape(m2, buffer)
    select_data = np.nanmean(select_data, axis=0)
    m2 = np.nanmean(m2, axis=0)
    # state_correction = np.average(state_correction, axis=0)
    fig, ax = plt.subplots()
    im = ax.pcolormesh(
        x, y, select_data, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
    )
    plt.title(f"Data #{i} ({select_data_rate*100:.1f}% x {reps:d})")
    ax.set_xticks([-2.0, 0.0, 2.0])
    ax.set_yticks([-2.0, 0.0, 2.0])
    ax.set_aspect("equal", "box")
    fig.tight_layout()
    plt.legend()
    plt.show()

# Use last sigma for scaling
x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1) / sig
y = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1) / sig

compiled_final_data = np.concatenate(final_data, axis=0)
nan_percentage = np.count_nonzero(np.isnan(compiled_final_data)) / len(
    compiled_final_data.flatten()
)
compiled_final_data = np.nanmean(compiled_final_data, axis=0)
fig, ax = plt.subplots()
im = ax.pcolormesh(
    x, y, compiled_final_data, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
plt.title(f"Repetitions: {(1-nan_percentage)*100:.1f}% x {total_reps:d}")
ax.set_aspect("equal", "box")
ax.set_xticks([-2.0, 0.0, 2.0])
ax.set_yticks([-2.0, 0.0, 2.0])
fig.tight_layout()
plt.show()
