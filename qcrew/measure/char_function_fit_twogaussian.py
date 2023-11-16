import matplotlib.pyplot as plt
import numpy as np

from qutip import *
import matplotlib as mpl
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap as lsc
import time
from matplotlib import gridspec
import scipy.optimize as opt


import h5py

input_file = "C:\\Users\\qcrew\\Desktop\\qcrew\\data\\somerset\\20230823\\144543_somerset_characteristic_function_2D.h5"
infile = h5py.File(input_file, "r")

data = np.array(infile["data"]["I_AVG"])
x = np.array(infile["data"]["x"][:, 0])
y = np.array(infile["data"]["y"][0, :])
infile.close()

# Helper functions

# list of values to create coherent states
def angles(points):
    points = [np.exp(1j*(np.pi*(1*x/points+1/4))) for x in range(points+1)]
    return points

# norm is minimal for max overlap
def norm(X, Y):
    return np.sum((X-Y)**2)

def sherlock(data,points):
    norms = []
    for i in range(len(points)):
        # step 1. calculate theoretical char func grid
        state = (tensor(coherent(N, points[i]),basis(2,0)))
        cf = char_func_grid(state,xvec) # xvec has to be consistent for theory and data!!!
        norms.append(norm(cf,data))
        print('Done with step', i)
    return norms

########################  2D plot ##################
import h5py
import matplotlib.pyplot as plt
import numpy as np
from qutip import*
import scipy.optimize as opt
# Everything in plae to be able to manipulate it quickly here if  needed.


N = 40
## cavity operators
a = tensor(destroy(N), qeye(2))
## qubit operator 
def char_func_grid(state, xvec):
    """Calculate the Characteristic function as a 2Dgrid (xvec, xvec) for a given state.

    Args:
        state (Qobject): State of which we want to calc the charfunc
        xvec (_type_): array of displacements. The char func will be calculated for the grid (xvec, xvec)

    Returns:
        tuple(ndarray, ndarray): Re(char func), Im(char func)
    """
    cfReal = np.empty((len(xvec),len(xvec)))
    cfImag = np.empty((len(xvec),len(xvec)))

    for i, alpha_x in enumerate(xvec):
        for j, alpha_p in enumerate(xvec):
            expect_value = expect(displace(N, alpha_x +1j*alpha_p),state)
            cfReal[i,j] =  np.real(expect_value)
            cfImag[i,j] =  np.imag(expect_value)

    return cfReal,cfImag  

def calc_squeez_parameter(dB):
    return np.log(10**(dB/10))/2

def twoD_Gaussian(xy_tuple, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    (x,y) = xy_tuple
    xo = float(xo)
    yo = float(yo)    
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) 
                            + c*((y-yo)**2)))
    return g.ravel()

initial_guess=(-0.3, 0,0, 0.5, 0.5, 0, 0)


popt, pcov = opt.curve_fit(twoD_Gaussian, (x,y), zscale.flatten(), p0=initial_guess)

fig, ax = plt.subplots(figsize = (5,5) )
ax.set_aspect('equal')
plt.pcolormesh(x, y, zscale, cmap = 'bwr',vmin=-1,vmax=1) # [4:31]
plt.colorbar()
plt.xlabel("X")
plt.ylabel('Y')
# plt.xticks(fontsize=18)
# plt.yticks(fontsize=18)
plt.title('Characteristic_function', fontsize=10)
data_fitted = twoD_Gaussian((x,y), *popt)
plt.contour(x,y, data_fitted.reshape(zscale.shape))
angle=popt[5]


# fig, axs = plt.subplots(1, 1, figsize=(20, 20))

# popts = []
# angles = []

# xvec = x  # i define it like this in case i want to slice x
# yvec = y
# X, Y = np.meshgrid(yvec, xvec)

# # (xy_tuple, amplitude, sigma_x, sigma_y, beta_amp, theta, offset)
# initial_guess = (np.max(data) - np.min(data), 0.8, 1, 1, 0.5, 0)  # upper blob

# popt, pcov = opt.curve_fit(char_func_fringe, (X, Y), data.flatten(), p0=initial_guess)
# popts.append(popt)
# angles.append(popt[4])

# data_fitted1 = char_func_fringe((X, Y), *popt)
# print(data.shape, yvec.shape, xvec.shape)
# axs.pcolormesh(yvec, xvec, data, cmap="seismic", shading="auto")
# axs.contour(yvec, xvec, data_fitted1.reshape(X.shape))
# axs.set_aspect("equal")
# axs.set_title(str(decay_times))

# plt.show()

# print("First Blob")
# print("amplitude:", popts[0][0])
# print("sigmax:", popts[0][1])
# print("sigmay:", popts[0][2])
# print("beta:", popts[0][3])
# print("theta:", (popts[0][4]))
# print("offset:", (popts[0][5]))
