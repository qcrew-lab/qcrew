import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = "C:/Users/qcrew/Desktop/qcrew/data/exitB_rr/20240205/201807_vnasweep_5500000000.0_-15pow_1reps.hdf5"
file = h5py.File(filepath, "r")
data = file["data"]
s21_mlog = data["s21_mlog"]
freqs = data["frequency"]
print(np.array(freqs).shape)
print(np.array(s21_mlog)[0].shape)
# s21_mlog_avg = np.mean(s21_mlog, axis=0)
plt.figure(figsize=(12, 8))
plt.plot(np.array(freqs), np.array(s21_mlog)[0])
plt.legend()
plt.show()
