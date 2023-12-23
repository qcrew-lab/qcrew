import matplotlib.pyplot as plt
import numpy as np
import h5py
from scipy.optimize import curve_fit

import os, sys
from os import listdir

# for experiment in data.keys():
    
def get_experiment_key(data, current, LO):
    
    for experiment in data.keys():
        exp_LO = float(np.array(data[experiment]["qubit_LO"]))
        exp_current = float(np.array(data[experiment]["current"]))
        if np.abs(exp_LO-LO)/LO < 0.01 and np.abs(exp_current-current)/np.abs(current) < 0.01:
            return experiment
        
    print("Could not find experiment with this LO and current")
    return 

def get_spec_data(data, exp_key):
    try:
        spec_data = data[exp_key]["Z_AVG"]
        print("Found Z_AVG data")
    except:
        spec_data = data[exp_key]["PHASE"]
        print("Found PHASE data")
        
    freq = data[exp_key]["freqs"]
    
    current = float(np.array(data[exp_key]["current"])) 
    LO = float(np.array(data[exp_key]["qubit_LO"])) 
    print("Experiment:", exp_key, "Current:", current, "LO:",  LO/1e9)
    
    return np.array(freq), np.array(spec_data)

def gaussian(x, mean, std, amp, off):
    return amp*np.exp(-(x-mean)**2/2/std**2) + off

def fit_spec_to_gaussian(freq, spec_data):
    # initial guesses
    p0_mean = freq[np.argmax(spec_data)]
    p0_std = 30e6
    p0_amp = np.max(spec_data) - np.min(spec_data)
    p0_off = np.average(spec_data)
    p0 = [p0_mean, p0_std, p0_amp, p0_off]

    popt, pcov = curve_fit(gaussian, freq, spec_data, p0=p0)
    return popt
    
def read_and_plot_data(filepath, current, LO):
    data = h5py.File(filepath, "r")["data"]
    exp_key = get_experiment_key(data, current, LO)
    freq, spec_data = get_spec_data(data, exp_key)
#     popt = fit_spec_to_gaussian(freq, spec_data)
    
    #qubit_freq = popt[0]
    
    # print data and fit
    plt.plot(freq, spec_data)
#     plt.plot(freq, [gaussian(f, popt[0], popt[1], popt[2], popt[3]) for f in freq])
    #plt.title("%.3fGHz" % (qubit_freq/1e9))
    plt.legend()
    plt.show()
    return 

filepath = "C:/Users/qcrew/Desktop/qcrew/data/somerset/20230508/011015_somerset_qubit_spec_current_sweep.h5"
LO = 5.0E9
current = -0.0068
read_and_plot_data(filepath, current, LO)