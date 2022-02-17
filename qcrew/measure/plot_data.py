import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = (
    "C:/Users/qcrew/Desktop/qcrew/data/cc2_transmon/20220204/143302_cc2_qubit_spec.h5"
)
file = h5py.File(filepath, "r")
data = file["data"]
z_avg = data["Z_AVG"]
x = data["x"]
plt.figure(figsize=(12, 8))
plt.plot(np.array(x), np.array(z_avg))
plt.show()
