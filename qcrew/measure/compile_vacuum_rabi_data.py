import h5py
import matplotlib.pyplot as plt
import numpy as np
import os


# filepath = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230711/150526_cut.h5"
folder_path = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230727/"
all_vacuum_rabi_files = [x for x in os.listdir(folder_path) if "castle" in x][:-1]
starting_time = "194547"
stoping_time = "212027"
vacuum_rabi_files = [
    x for x in all_vacuum_rabi_files if int(stoping_time) >= int(x.split("_")[0]) >= int(starting_time)
]


amp_sweep = None
flux_len_list = np.arange(4, 301, 8)[: len(vacuum_rabi_files)]
I_AVG_matrix = []

for filepath in vacuum_rabi_files:
    file = h5py.File(folder_path + filepath, "r")
    data = file["data"]
    I_AVG_matrix.append(np.array(data["I_AVG"]))
    amp_sweep = np.array(data["internal sweep"])

I_AVG_matrix = np.array(I_AVG_matrix)  # np.flip(np.array(I_AVG_matrix), axis=0)
plt.pcolormesh(amp_sweep, flux_len_list, I_AVG_matrix)
plt.show()
# plt.figure(figsize=(8, 5))
# file = h5py.File(filepath, "r")
# data = file["data"]
# print(data.keys())
# state = data["I_AVG"]  # data["PHASE"] Z_AVG
# x = data["x"]
# print(len(state))
# # print(np.where(x == -95000000))
# # print(x[150])

# plt.plot(np.array(x), np.array(state))
# plt.show()

# filepath_list = [
#     "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230503/173031_somerset_rr_spec.h5",
# ]
# plt.figure(figsize=(8, 5))
# for i, filepath in enumerate(filepath_list):
#     file = h5py.File(filepath, "r")
#     data = file["data"]
#     z_avg = data["Z_AVG"]  # data["PHASE"]
#     x = data["x"]
#     f = x[:,0]
#     for trace in (np.array(z_avg).T): #[:3]
#         trace = trace - np.average(trace)
#         print(f[np.argmin(trace)])
#         plt.plot(np.array(f), np.array(trace))
#     plt.ylabel("Z_AVG")  # phase
#     plt.xlabel("IF frequency (Hz)")  # . Qubit LO = 1.4 GHz")
#     plt.title(filepath_list)
#     plt.show()
