from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit
from numpy import linalg as LA


def reshape_and_avg(data_array, buffer):
    return np.average(np.reshape(data_array, buffer), axis=0)


def correct_ofs_and_amp(data_array, amp, ofs):
    return (data_array - ofs) / amp


def gaussian(x, a, b, sigma, c):
    return a * np.exp(-((x - b) ** 2) / (2 * sigma ** 2)) + c


def gaussian_fit(x, y):
    popt, pcov = curve_fit(
        gaussian,
        x,
        y,
        bounds=(
            (-np.inf, min(x), -np.inf, -np.inf),
            (np.inf, max(x), np.inf, np.inf),
        ),
        p0=[max(y) - min(y), 0, 0.5, max(y)],
    )
    return popt


def characteristic_coherent(xy, A, B, C, alpha, theta):
    x = xy[:, 0]
    y = xy[:, 1]
    envelope = np.exp(-(A * x ** 2 + 2 * B * x * y + C * y ** 2))
    # envelope = np.exp(-(x ** 2) / 2 / A ** 2) * np.exp(-(y ** 2) / 2 / B ** 2)
    oscillation = np.exp(
        1j * y * alpha * np.cos(theta) - 1j * x * alpha * np.sin(theta)
    )
    return np.imag(envelope * oscillation)


def characteristic_coherent_fit(x, y, z, bounds, guess):
    popt, pcov = curve_fit(
        characteristic_coherent,
        (x, y),
        z,
        bounds=bounds,
        p0=guess,
    )
    return popt


cal_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231115/175703_somerset_characteristic_function_1D_ff.h5"
data_filename = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231115/200535_somerset_characteristic_function_2D_chi_evolve.h5"

threshold = -0.00014579810270391258

# Get offset and amplitude from 1D vacuum data
file = h5py.File(cal_filename, "r")
data = file["data"]
state_correction = np.array(data["state"])[:, 0]
# ((np.array(data["I"])) < threshold).astype(int)
# state_correction = np.average(state_correction, axis=0)
# x = np.arange(-1.9, 1.91 + 0.1 / 2, 0.1)
x = np.array(data["x"][:, 0])  # np.arange(-1.2, 1.21 + 0.08 / 2, 0.08)
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
print(ofs)
file = h5py.File(data_filename, "r")
data = file["data"]
state = np.array(data["state"])#.T # transpose to 90 degree
x = np.array(data["x"][:,0]) 
y = np.array(data["y"][0,:]) 
# state = (np.array(data["I"]) < threshold).astype(int)
# state = state.flatten()  # revert the buffering of qcore
file.close()

# separate internal loop into even (0.0) and odd (0.5) and state

# Get x and y sweeps for buffering and plotting
state_corrected = correct_ofs_and_amp(state, amp, ofs)
x = x / sig
y = y / sig

# Get fit
x_mesh, y_mesh = np.meshgrid(x, y)
xdata = np.c_[x_mesh.flatten(), y_mesh.flatten()]
ydata = state_corrected.flatten()
bounds = [
    (0.0, 0.0, 0.0, 0.0, 2 * np.pi * 0.00),
    (3, 0.5, 3, 6, 2 * np.pi * 1),
]  # (_, A, B, C, alpha, theta)
guess = (0.5, 0, 0.5, 3, 2 * np.pi * 0.0)

popt, pcov = curve_fit(
    characteristic_coherent,
    xdata,
    ydata,
    bounds=bounds,
    p0=guess,
)
state_fit = characteristic_coherent(xdata, *popt).reshape(len(y), len(x))

# Final plot and fit
fig, ax = plt.subplots()

print(popt)

ax.set_aspect("equal", "box")
fig.tight_layout()
# sm = ax.imshow(state_fit, cmap=plt.get_cmap("coolwarm"), origin="lower")
A, B, C = popt[:3]
cov_matrix = np.array([[A, B], [B, C]])
lamb1, lamb2 = LA.eig(cov_matrix)[0]
sig1, sig2 = 1 / (2 * lamb1) ** 0.5, 1 / (2 * lamb2) ** 0.5
print(sig1, sig2)
label_txt = (
    f"sig1: {sig1:.2f}, sig2: {sig2:.2f}\n|a|: {popt[3]:.3f}, theta: {popt[4]:.3f}"
)
print(label_txt)
CS = ax.contour(x_mesh, y_mesh, state_fit, levels=[-0.9, -0.5, -0.1, 0.1, 0.5, 0.9])
im = ax.pcolormesh(
    x,
    y,
    state_corrected,
    norm=colors.Normalize(vmin=-1, vmax=1),
    cmap="bwr",
)
plt.title(label_txt)
plt.show()
