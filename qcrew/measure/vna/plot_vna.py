import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = (
    "C:/Users/qcrew/Desktop/qcrew/data/Aquarius/20220726/190311_ampfluxsweep_.hdf5"
)
file = h5py.File(filepath, "r")
data = file["data"]
s21_phase = data["s21_phase"]
freqs = data["frequency"]
s21_phase_avg = np.mean(s21_phase, axis=0)
plt.figure(figsize=(12, 8))
plt.plot(np.array(freqs), s21_phase_avg[0])
plt.legend()
plt.show()
