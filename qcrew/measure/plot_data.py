import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = r"D:\data\YABBAv4\20230923\150806_YABBA_power_rabi.h5"
file = h5py.File(filepath, "r")
data = file["data"]
I = data["I"]
x = data["x"]

threshold = -0.00014956578372339103

I_first= I[::]
I_second = I[1::2]

ss = False

if ss:
    I_first = [[int(cell) for cell in row] for row in (I_first>threshold)]
    I_second = [[int(cell) for cell in row] for row in (I_second>threshold)]

I_AVG_first = np.average(I_first, axis = 0)
I_AVG_second = np.average(I_second, axis = 0)

# print(I_second)

plt.figure(figsize=(12, 8))
plt.plot(I_first[0])
plt.plot(I_first[1])
plt.plot(I_first[2])
plt.plot(I_first[3])
plt.show()

