import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath_list = [
    "C:/Users/qcrew/Desktop/qcrew/data/exitB/20230307/200709_somerset_qubit_spec.h5",
]
plt.figure(figsize=(8, 5))
for i, filepath in enumerate(filepath_list):
    file = h5py.File(filepath, "r")
    data = file["data"]
    z_avg = data["PHASE"]
    x = data["x"]
    plt.plot(np.array(x), np.array(z_avg))
    plt.ylabel("phase")
    plt.xlabel("IF frequency (Hz). Qubit LO = 2.6 GHz")
    plt.show()