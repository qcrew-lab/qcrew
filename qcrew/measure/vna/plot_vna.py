import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = rf"C:\Users\qcrew\Desktop\qcrew\data\cheddar\20240206\153812_vnasweep_6000000000.0_-15pow_1reps.hdf5"
file = h5py.File(filepath, "r")
data = file["data"]
s21_mlog = data["s21_mlog"]
freqs = data["frequency"]
s21_mlog_avg = np.mean(s21_mlog, axis=0)
plt.figure(figsize=(12, 8))
plt.plot(np.array(freqs), s21_mlog_avg[0])
plt.legend()
plt.show()
