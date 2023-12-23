from random import gauss
from re import X
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy.optimize import curve_fit

filename_A ="C:/Users/qcrew/Desktop/qcrew/data/somerset/20231127/222912_somerset_cavity_spec.h5"


file = h5py.File(filename_A, "r")
data = file["data"]
state1 = -np.array(data["I_AVG"])  # data["PHASE"]
# y1 = np.array(data["y"])  # data["PHASE"]
x1 = np.array(data["x"])
file.close()

plt.plot(x1, state1)

plt.show()