import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = "Z:/TK/Experimental data/140433_YABBA_wigner_function_pi_vacuum.h5"
file = h5py.File(filepath, "r")
data = file["data"]
z = data["I_AVG"]
x = data["x"]
y = data["y"]

x0 = x[:, 0]
y0 = y[0, :]

# plt.figure(figsize=(12, 8))
# plt.imshow(np.rot90(np.array(z)), extent=[x0[0], x0[-1], y0[0], y0[-1]], cmap="bwr")
# plt.colorbar()

# plt.show()