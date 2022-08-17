# from statistics import covariance
# from msilib.schema import Font
# from tkinter import font
# from turtle import color
from msilib.schema import Font
from tkinter import font
import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from qcrew.analyze import fit


########################  1D plot ##################

# def func(xs, amp, alpha0, tau, ofs, n):
#     '''
#     Poissonian distribution given photon projection:
#     alpha = alpha0 * exp(-xs / tau)
#     '''
#     alphas = alpha0 * np.exp(-xs / 2.0 / tau)
#     nbars = alphas**2
#    # return ofs + amp * nbars**n / math.factorial(int(n)) * np.exp(-nbars)
#     return ofs + amp * nbars**n / 1 * np.exp(-nbars)



# filepath = (
#     "C:/Users/qcrew/Desktop/qcrew/data/panther_transmon/20220720/215742_panther_cavity_T1.h5"
# )
# file = h5py.File(filepath, "r")
# data = file["data"]
# x_vec = data["x"][:] * 4  # now x_vec is ns
# I_avg = data["I_AVG"][:]

# fit_func = 'cohstate_decay'
# params = fit.do_fit(fit_func, x_vec, I_avg)
# fit_ys = fit.eval_fit(fit_func, params, x_vec)
# fig, ax = plt.subplots(figsize = (12, 8))

# ###calculate errorbar
# i = data['I'][:]
# q = data['Q'][:]
# d = np.sqrt(i**2 + q**2)
# err = np.std(d)/np.sqrt(d.shape[0])

# plt.errorbar(np.array(x_vec), np.array(I_avg), yerr=err, fmt = 'o', color = 'blue', ecolor= 'blue' )
# plt.plot(x_vec, fit_ys, color='black', lw=3)
# plt.xlabel("Cavity relaxation time (ns)", fontsize = 18)
# plt.ylabel("Signal (a.u.)", fontsize = 18)
# plt.title("Cavity T1",fontsize = 18)
# plt.xticks(fontsize=18)
# plt.yticks(fontsize=18)
# plt.savefig("C:/Users/qcrew/Desktop/Cavity_T1.pdf")



# ########################  2D plot ##################
# import h5py
# import matplotlib.pyplot as plt
# import numpy as np


# filepath = (
#     "C:/Users/qcrew/Desktop/qcrew/data/panther_transmon/20220728/130200_panther_ECD_characteristic_func.h55"
# )
# file = h5py.File(filepath, "r")
# data = file["data"]
# x_vec = np.arange(-1.8, 1.8 + 0.1/2, 0.1)
# y_vec = np.arange(-1.8, 1.8 + 0.1/2, 0.1)

# I = np.array(data["I"])
# Q = np.array(data["Q"])

# I_AVG = data["I_AVG"]
# fig, ax = plt.subplots(figsize = (9,6))
# plt.pcolormesh(x_vec, y_vec, I_AVG, cmap = 'bwr', shading='auto' )
# plt.title('measured')


# #### calculate the Z_AVG
# d_avg = np.average(I, axis=0)
# Z = np.reshape(d_avg, (31, 31))
# fig, ax = plt.subplots(figsize = (9,6) )
# plt.pcolormesh(x_vec, y_vec, Z, cmap = 'bwr', shading='auto' )
# plt.title('calculated')


#ax.set_aspect("equal")
# componsate the missing data of I and Q

# I_new  = np.column_stack((I, I[:, 1084]))
# I_new1 = np.column_stack((I_new, I[:, 1084]))
# I_new2 = np.column_stack((I_new1, I[:, 1084]))
# I_new3 = np.column_stack((I_new2, I[:, 1084]))
    

# Q_new  = np.column_stack((Q, Q[:, 1084]))
# Q_new1 = np.column_stack((Q_new, Q[:, 1084]))
# Q_new2 = np.column_stack((Q_new1, Q[:, 1084]))
# Q_new3 = np.column_stack((Q_new2, Q[:, 1084]))
    
# Z = np.zeros((5879, 1089))

# for n in range(1000):
#     Z[n,:] = np.sqrt(I_new3[n,:]**2 + Q_new3[n,:]**2)
    
# Z_new = np.sqrt(I**2 + Q**2)


# Z_avg = np.average(Z, axis = 0) # sum the rows

# Z_avg_new = np.reshape(Z_avg, (33, 33))

# fig, ax =  plt.subplots(figsize = (12,6))
# ax.pcolormesh(x_vec, y_vec, Z_avg_new, cmap = 'bwr', shading='auto')
# ax.set_xlabel("X")
# ax.set_ylabel("Y")
# ax.set_aspect("equal")
# ax.set_title("Q function")




########################  2D plot ##################
# import h5py
# import matplotlib.pyplot as plt
# import numpy as np


# filepath = (
#     "C:/Users/qcrew/Desktop/qcrew/data/lion_transmon/20220316/002347_lion_characteristic_function.h5"
# )
# file = h5py.File(filepath, "r")
# data = file["data"]
# x_vec = np.arange(-1.5, 1.5 + 0.05/2, 0.05)
# y_vec = np.arange(-1.5, 1.5 + 0.05/2, 0.05)

# I = np.array(data["I"])
# Q = np.array(data["Q"])

# d = np.sqrt(I**2 + Q**2)

# #### calculate the Z_AVG
# d_avg = np.average(d, axis=0)
# Z = np.reshape(d_avg, (61, 61)).T
# zs = ((Z - Z.min())/(Z - Z.min()).max())*2-1
# fig, ax = plt.subplots(figsize = (9,9) )
# plt.pcolormesh(x_vec[9:52], y_vec[9:52], zs[9:52, 9:52], cmap = 'bwr',vmin=-1, vmax=1)
# plt.xlabel("X", fontsize = 18)
# plt.ylabel('Y', fontsize = 18)
# plt.xticks(fontsize=18)
# plt.yticks(fontsize=18)
# plt.title('Characteristic_function', fontsize=18)
# plt.savefig("C:/Users/qcrew/Desktop/characteristic_function.pdf")


# ########################  1D plot ##################
import h5py
import matplotlib.pyplot as plt
import numpy as np


filepath = (
    "C:/Users/qcrew/Desktop/qcrew/data/panther_transmon/20220812/103308_panther_power_rabi.h5"
)
file = h5py.File(filepath, "r")
data = file["data"]
x = np.array(data['x'][:,0])
state1 = np.array(data['state'][:,0])
state2 = np.array(data['state'][:,1])
print(state1)
plt.plot(x, state1,'r*')
plt.plot(x, state2, 'bo')

# I_AVG = data["I_AVG"]
# fig, ax = plt.subplots()
# # ax.pcolormesh(x_vec, y_vec, I_AVG, cmap = 'bwr', shading='auto' )
# ax.plot(x_vec, I_AVG[:,19])
# ax.set_title('measured')
# ax.set_aspect("equal")
