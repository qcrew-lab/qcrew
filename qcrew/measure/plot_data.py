import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = (
    "C:/Users/qcrew/Desktop/qcrew/data/lion_transmon/20220304/110559_lion_rr_amp_calibration.h5"
)
file = h5py.File(filepath, "r")
data = file["data"]
z_avg = data["Z_AVG"]
x = data["x"]
plt.figure(figsize=(12, 8))
plt.plot(np.array(x), np.array(z_avg))
plt.show()

a=[]
for i in range(25):
    print(z_avg[i][0]-z_avg[i][1])
    a.append(z_avg[i][0]-z_avg[i][1])
   
print(min(a))
print(x[16])