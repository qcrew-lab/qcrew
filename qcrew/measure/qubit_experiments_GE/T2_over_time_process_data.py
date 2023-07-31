# from statistics import covariance
# from msilib.schema import Font
# from tkinter import font
# from turtle import color
from msilib.schema import Font
from tkinter import font
import h5py
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from qcrew.analyze import fit


# assign directory
directory = 'C:/Users/qcrew/Desktop/qcrew/data/yabba/findingymon'
 
# iterate over files in
# that directory
files = Path(directory).glob('*')

index = np.linspace(0, 1, 382)
i = 0
for file in files:
    file = 'D:/data/YABBAv4/141532_YABBA_rr_amp_calibration.h5'
    curr = h5py.File(file, "r")
    data = curr["data"]
    try:
        x_vec = data["x"][:]
    except KeyError:
        print(file)
        print("**************x error************")
    try:
        i_avg = data["Z_AVG"][:]
    except KeyError:
        print(file)
        print("*************iavg error************")
    # fit_func = 'exp_decay_sine'
    # params = fit.do_fit(fit_func, x_vec, i_avg)
    # fit_ys = fit.eval_fit(fit_func, params, x_vec)
    i += 1
    plt.plot(x_vec, i_avg, '-o' )

    print(i)
    plt.show()


    


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