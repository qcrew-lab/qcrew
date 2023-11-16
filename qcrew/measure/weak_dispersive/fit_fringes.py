########################  2D plot ##################
import h5py
import matplotlib.pyplot as plt
import numpy as np
from qutip import *
import scipy.optimize as opt


def twoD_Gaussian(xy_tuple, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    (x, y) = xy_tuple
    xo = float(xo)
    yo = float(yo)
    a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (
        2 * sigma_y ** 2
    )
    b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (
        4 * sigma_y ** 2
    )
    c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (
        2 * sigma_y ** 2
    )
    g = offset + amplitude * np.exp(
        -(a * ((x - xo) ** 2) + 2 * b * (x - xo) * (y - yo) + c * ((y - yo) ** 2))
    )
    return g.ravel()


# get data
file_address = "C:\\Users\\qcrew\\Desktop\\qcrew\\data\\somerset\\20230824\\"
file_name = "111340_somerset_characteristic_function_2D.h5"
input_file = file_address + file_name
infile = h5py.File(input_file, "r")  # 144543, 153851

z = np.array(infile["data"]["I_AVG"])
x = np.array(infile["data"]["x"][:, 0])
y = np.array(infile["data"]["y"][0, :])
infile.close()

# rescale data matrix to 1 to -1
def scale(col, min, max):
    range = col.max() - col.min()
    a = (col - col.min()) / range
    return a * (max - min) + min


zscale = scale(z, -1, 1)
zscale = zscale.T

xvec = x  # i define it like this in case i want to slice x
yvec = y
X, Y = np.meshgrid(yvec, xvec)

# amplitude, xo, yo, sigma_x, sigma_y, theta, offset
initial_guess = (-0.3, 0, 0, 0.5, 0.5, 0, 0)
popt, pcov = opt.curve_fit(twoD_Gaussian, (X, Y), zscale.flatten(), p0=initial_guess)

fig, ax = plt.subplots(figsize=(5, 5))
ax.set_aspect("equal")
plt.pcolormesh(X, Y, zscale, cmap="bwr")  # [4:31]
plt.colorbar()
plt.xlabel("X")
plt.ylabel("Y")
# plt.xticks(fontsize=18)
# plt.yticks(fontsize=18)
plt.title(file_name, fontsize=10)
data_fitted = twoD_Gaussian((X, Y), *popt)
plt.contour(yvec, xvec, data_fitted.reshape(X.shape))
rad_angle = popt[5]

print("amplitude:", popt[0])
print("x0:", popt[1])
print("y0:", popt[2])
print("sigma_x:", popt[3])
print("sigma_y:", (popt[4]))
print("theta:", (popt[5]))
print("offset:", (popt[6]))

# degree_angle = rad_angle*180/np.pi-180
degree_angle = -rad_angle * 180 / np.pi
print("translate to angle", degree_angle)
print("translate to tomo phase", -0.25 * degree_angle / 90)

plt.show()
