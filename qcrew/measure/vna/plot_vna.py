import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = "C:/Users/qcrew/Desktop/qcrew/data/LION/20220509/135209_vnasweep_7.455000E+09GHz.hdf5"
file = h5py.File(filepath, "r")
data = file["data"]
s21_mlog = data["s21_mlog"]
freqs = data["frequency"]
power = data["power1"]
s21_mlog_avg = np.mean(s21_mlog, axis=0)
plt.figure(figsize=(12, 8))
for i, trace in enumerate(s21_mlog_avg):
    plt.plot(np.array(freqs), trace, label=power[i])
plt.legend()
plt.show()
