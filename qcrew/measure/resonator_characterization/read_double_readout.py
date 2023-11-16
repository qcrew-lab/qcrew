# two measurements
import h5py
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from qcrew.control import Stagehand

filepath = (
    "C:/Users/qcrew/Desktop/qcrew/data/somerset/20231030/152342_somerset_power_rabi.h5"
)

file = h5py.File(filepath, "r")
data = file["data"]
data_i = data["I"][:]

with Stagehand() as stage:
    thresh = stage.RR.readout_pulse.threshold

ss_data = np.where(data_i < thresh, 1, 0)
# proj e: 1 (data_i < thresh)
# proj g: 0 (data_i > thresh)

ss_data = ss_data.flatten()
# m1 = ss_data[:, 0]
# m2 = ss_data[:, 1]
m1 = ss_data[::2]
m2 = ss_data[1::2]

mx_e = ma.masked_array(m2, mask=m1)
mx_g = ma.masked_array(m2, mask=np.logical_not(m1))

print(m1[:20])
print(m2[:20])

print(filepath)
print("\nP(m1:g) = ", 1 - m1.mean(axis=0))
print("P(m1:e) = ", m1.mean(axis=0))
print("P(m2:g) = ", 1 - m2.mean(axis=0))
print("P(m2:e) = ", m2.mean(axis=0))
print("P(m2:g|m1:g) = ", 1 - np.average(ma.masked_array(m2, mask=m1)))
print("P(m2:g|m1:e) = ", 1 - np.average(ma.masked_array(m2, mask=np.logical_not(m1))))
print("P(m2:e|m1:g) = ", np.average(ma.masked_array(m2, mask=m1)))
print("P(m2:e|m1:e) = ", np.average(ma.masked_array(m2, mask=np.logical_not(m1))))
