import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = "D:/data/YABBAv4/20230916/121857_YABBA_rr_spec_dispersive_shift.h5"
file = h5py.File(filepath, "r")
data = file["data"]
I_raw = np.array(data["I"])
Q_raw = np.array(data["Q"])
# print(I_raw[1, :].shape)  # freq
# print(I_raw[:, 1].shape)  # repetition
I_avg = I_raw.mean(axis=0)  # column
Q_avg = Q_raw.mean(axis=0)  # column
Z_avg = I_avg**2 + Q_avg**2
x_start = 48e6
x_stop = 52e6
x_step = 0.1e6

x = np.arange(int(x_start), int(x_stop + x_step / 2), int(x_step))

plt.plot(x, Z_avg, "")
plt.title(filepath)

print(x[Z_avg.argmin()])
