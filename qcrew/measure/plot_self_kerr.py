# -*- coding: utf-8 -*-
"""
Created on Wed Sep 13 16:05:39 2023

@author: spt
E-mail: ptsong@nus.edu.sg
"""

import numpy as np
import h5py
import matplotlib.pyplot as plt
from scipy import optimize
from numpy import pi
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# unit is us and MHz


def loadh5(filename):
    h5 = h5py.File(filename, "r")
    keys = list(h5.keys())
    data = h5["data"]
    keys_data = list(data.keys())
    output = {}
    for key in keys_data:
        if key == "I":
            output["I"] = np.array(data["I"])
        elif key == "Q":
            output["Q"] = np.array(data["Q"])
        elif key == "x":
            output["x"] = np.array(data["x"])
        elif key == "y":
            output["y"] = np.array(data["y"])
        elif key == "state":
            output["P"] = np.array(data["state"])  # state
        else:
            pass
    return output


class fit_selfKerr(object):
    def __init__(self, alpha, omega, scaling_flag=True):
        self.alpha = alpha
        self.omega = omega
        self.scaling_flag = scaling_flag

    def Pfunction(self, t, fre, offset, scaling):
        alpha = self.alpha
        omega = 2 * pi * self.omega
        delta = 0
        n = alpha ** 2
        if self.scaling_flag == True:
            p = offset + scaling * np.exp(-2 * n * (1 - np.cos((omega + fre) * t)))
        else:
            p = np.exp(-2 * n * (1 - np.cos((omega + fre) * t)))

        return p

    def fitPfunction(self, xData, yData):
        fre_0 = 2e-3
        offset_0 = 0
        scaling_0 = 1
        p0 = [fre_0, offset_0, scaling_0]
        fre, offset, scaling = optimize.curve_fit(self.Pfunction, xData, yData, p0=p0)[
            0
        ]

        return fre, offset, scaling

    def fitSfunction_alldata(self, xData, yData):
        fre, offset, scaling = self.fitPfunction(xData, yData)
        xfit = np.linspace(np.min(xData), np.max(xData), 4 * (len(xData) - 1) + 1)
        yfit = self.Pfunction(xfit, fre, offset, scaling)
        return [[fre, offset, scaling], [xfit, yfit]]


filename = (
    r"C:\Users\qcrew\Desktop\qcrew\data\somerset\20231102\194440_somerset_Self_Kerr.h5"
)
# 185150_somerset_Self_Kerr.h5
# filename = r'C:\Users\qcrew\Downloads\230149_YABBA V3_Self_Kerr.h5'
#
data = loadh5(filename)
omega = 20  # 0.5 #16 # unit is MHz

t = data["x"][:, 0] * 4 / 1000  # ns => us


alphalist = data["y"][0, :]


p = data["P"]  # -

p0 = p[:, 0]
p1 = p[:, 1]
p2 = p[:, 2]
p3 = p[:, 3]

plt.figure()
for i in range(p.shape[1]):
    plt.plot(t, p[:, i], label=r"$\alpha$ = {}".format(alphalist[i]))
    plt.legend()


colorlist = ["r", "b", "g", "c", "m", "y", "orange", "tan"]

frelist = []
plt.figure()
for i in range(len(alphalist)):
    xData = t[:]
    yData = p[:, i][:]

    fit = fit_selfKerr(alpha=alphalist[i], omega=omega, scaling_flag=False)
    fitdata = fit.fitSfunction_alldata(xData, yData)
    frelist.append(fitdata[0][0] / (2 * np.pi))

    plt.scatter(
        xData,
        yData + i,
        c=colorlist[i],
        s=10,
        label=r"$\alpha$ = {}".format(alphalist[i]),
    )
    plt.plot(fitdata[1][0], fitdata[1][1] + i, c="k")
    plt.xlabel(r"Time ($\mu$s)")
    plt.ylabel(r"Pe + i")
    plt.legend()
plt.show()

frelist = np.array(frelist)


nbar_cut = alphalist ** 2
selfKerr_cut = frelist * 1000

linearfit = np.polyfit(nbar_cut, selfKerr_cut, deg=1)
yfitf_f = np.poly1d(linearfit)
xfit = np.linspace(0, 4, 41)

plt.figure()
plt.scatter(nbar_cut, selfKerr_cut, s=20)

plt.plot(xfit, yfitf_f(xfit), c="k")
plt.xlabel(r"$\bar{n}$")
plt.ylabel(r"Frequency (kHz)")
plt.text(0, 10, "slop = {} \n offset = {}".format(linearfit[0], linearfit[1]))
