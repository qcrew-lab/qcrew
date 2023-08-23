from turtle import tracer
import h5py
import matplotlib.pyplot as plt
import numpy as np

# filepath = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230711/150526_cut.h5"
filepath = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230816/165224_somerset_ramsey_revival.h5"

plt.figure(figsize=(8, 5))
file = h5py.File(filepath, "r")
data = file["data"]
print(data.keys())
state = data["I_AVG"]  # data["PHASE"] Z_AVG
x = data["x"]
print(len(state))
# print(np.where(x == -95000000))
# print(x[150])

plt.plot(np.array(x), np.array(state))
plt.show()

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
