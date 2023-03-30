import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath_list = [
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230327/122921_somerset_qubit_spec.h5",
]
plt.figure(figsize=(8, 5))
for i, filepath in enumerate(filepath_list):
    file = h5py.File(filepath, "r")
    data = file["data"]
    z_avg = data["Z_AVG"] #data["PHASE"]
    x = data["x"]
    plt.plot(np.array(x), np.array(z_avg))
    plt.ylabel("Z_AVG") #phase
    plt.xlabel("IF frequency (Hz). Qubit LO = 1 GHz")
    plt.title(filepath_list)
    plt.show()