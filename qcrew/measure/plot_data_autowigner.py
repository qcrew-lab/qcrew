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


wigner_calibration_list = (
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/160440_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/165511_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/175556_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/190334_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/202234_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/222038_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/232647_somerset_wigner_1d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231017/003032_somerset_wigner_1d.h5",
)

filepath_list = [
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/161939_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/171210_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/181404_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/193655_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/203858_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/223536_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231016/235515_somerset_wigner_2d.h5",
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231017/004541_somerset_wigner_2d.h5",
]

threshold = -0.00014472961900504353

vacuum_corrected = []
fock1_corrected = []
fock2_corrected = []

for i in range(len(filepath_list)):
    cal_filename = wigner_calibration_list[i]
    data_filename = filepath_list[i]

    ### Get amplitude and offset
    file = h5py.File(cal_filename, "r")
    data = file["data"]
    state_correction_A = np.array(data["state"][:, 0])
    state_correction_B = np.array(data["state"][:, 1])
    state_correction = state_correction_A - state_correction_B
    x = np.array(data["x"][:, 0])
    file.close()
    fig, ax = plt.subplots()
    im = ax.scatter(x, state_correction, label="data")
    popt = gaussian_fit(x, state_correction)
    y_fit = gaussian(x, *popt)
    amp = popt[0]
    sig = popt[2]
    ofs = popt[3]
    ax.plot(x, y_fit, label=f"amp = {amp:.3f}\nsig = {sig:.3f}\nofs = {ofs:.3f}")

    plt.title(f"1D Wigner for amplitude and offset correction #{i}")
    plt.legend()

    file = h5py.File(data_filename, "r")
    data = file["data"]
    state = (np.array(data["I"]) < threshold).astype(int)
    state = state.flatten()  # revert the buffering of qcore

    # separate internal loop into even (0.0) and odd (0.5) and state
    even_vacuum = state[::6]
    odd_vacuum = state[1::6]
    even_fock1 = state[2::6]
    odd_fock1 = state[3::6]
    even_fock2 = state[4::6]
    odd_fock2 = state[5::6]

    # Get x and y sweeps for buffering and plotting
    y = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
    x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
    # reps for buffering and averaging
    reps = len(even_vacuum) // (len(y) * len(x))
    buffer = (reps, len(y), len(x))

    even_vacuum_avg = np.average(np.reshape(even_vacuum, buffer), axis=0)
    odd_vacuum_avg = np.average(np.reshape(odd_vacuum, buffer), axis=0)
    even_fock1_avg = np.average(np.reshape(even_fock1, buffer), axis=0)
    odd_fock1_avg = np.average(np.reshape(odd_fock1, buffer), axis=0)
    even_fock2_avg = np.average(np.reshape(even_fock2, buffer), axis=0)
    odd_fock2_avg = np.average(np.reshape(odd_fock2, buffer), axis=0)

    # fig, ax = plt.subplots(3, 2)

    # im = ax[0, 0].pcolormesh(x, y, even_vacuum_avg, cmap="bwr")
    # im = ax[0, 1].pcolormesh(x, y, odd_vacuum_avg, cmap="bwr")

    # im = ax[1, 0].pcolormesh(x, y, even_fock1_avg, cmap="bwr")
    # im = ax[1, 1].pcolormesh(x, y, odd_fock1_avg, cmap="bwr")

    # im = ax[2, 0].pcolormesh(x, y, even_fock2_avg, cmap="bwr")
    # im = ax[2, 1].pcolormesh(x, y, odd_fock2_avg, cmap="bwr")

    # fig.suptitle("Uncorrected plots")
    # plt.show()

    vacuum_corrected.append(((even_vacuum_avg - odd_vacuum_avg) - ofs) / amp)
    fock1_corrected.append(((even_fock1_avg - odd_fock1_avg) - ofs) / amp)
    fock2_corrected.append(((even_fock2_avg - odd_fock2_avg) - ofs) / amp)

vacuum_final = np.average(vacuum_corrected, axis=0)
fock1_final = np.average(fock1_corrected, axis=0)
fock2_final = np.average(fock2_corrected, axis=0)

# Final Fock 0, 1, 2 wigner plots
fig, ax = plt.subplots(1, 3)

im = ax[0].pcolormesh(
    x, y, vacuum_final, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[1].pcolormesh(
    x, y, fock1_final, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
im = ax[2].pcolormesh(
    x, y, fock2_final, norm=colors.Normalize(vmin=-1, vmax=1), cmap="bwr"
)
ax[0].set_title(f"max = {np.max(vacuum_final):.3f}\nmin = {np.min(vacuum_final):.3f}")
ax[1].set_title(f"max = {np.max(fock1_final):.3f}\nmin = {np.min(fock1_final):.3f}")
ax[2].set_title(f"max = {np.max(fock2_final):.3f}\nmin = {np.min(fock2_final):.3f}")

ax[0].set_aspect("equal", "box")
ax[1].set_aspect("equal", "box")
ax[2].set_aspect("equal", "box")

fig.tight_layout()

plt.legend()
plt.show()

plt.plot(x, vacuum_final[len(x) // 2, :])
plt.plot(x, fock1_final[len(x) // 2, :])
plt.plot(x, fock2_final[len(x) // 2, :])
plt.grid()
plt.show()
