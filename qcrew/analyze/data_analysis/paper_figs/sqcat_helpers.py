import h5py
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import os
from qutip import*
import matplotlib as mpl
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap as lsc
import time
from matplotlib.pyplot import figure, show
from matplotlib import gridspec
from plotconfig import*
from collections import defaultdict

def batch_load_data(d, fname, scale=3, file_range=None):
    
    fps = []
    fp1 = ([d + f for f in os.listdir(d) if f.endswith(fname +'.h5')])
    fp1.sort(key=lambda x: os.path.getmtime(x))

    if file_range is not None:
        fps = fp1[file_range[0]:file_range[1]]
    else:
        fps = fp1

    results = defaultdict(lambda: defaultdict(dict))
    dts = []
    for kk in range(len(fps)):
        df = h5py.File(fps[kk], "r")
        data = df["data"]
        data_i = data["I"][:]
        sweep_points = data["x"]
        data_dims = np.ndim(sweep_points)
        if data_dims == 1:
            x = data["x"][:]# * scale
            ax_data = [x]
        else:
            x = data["x"][:, 0, 0] #* scale
            y = data["y"][0, :, 0] #* scale
#             ax_data = np.vstack([x,y])
            ax_data = [x, y]
            
        dt = df.attrs['decay_time']/1e3
        results[int(kk)][int(dt)]  = data_i   

    return results, ax_data

def threhold_mask_data(data_array, thresh_val, ax_data):
    
    thresh = thresh_val
    
    if len(ax_data) ==2:
        x = ax_data[0]
        y = ax_data[1]
        
    raw_m0 = data_array[:, 0::3]
    raw_m1 = data_array[:, 1::3] 
    raw_m2 = data_array[:, 2::3]

    m0 = np.where(raw_m0 < thresh, 1, 0)
    m1 = np.where(raw_m1 < thresh, 1, 0)
    m2 = np.where(raw_m2 < thresh, 1, 0)

    m1_g = ma.masked_array(m1, mask=m0)
    m2_g = ma.masked_array(m2, mask=m0)

    double_ps_g = ma.masked_array(m2_g, mask=m1).mean(axis=0).reshape(len(x), len(y)) * 2 - 1
    double_ps_e = ma.masked_array(m2_g, mask=np.logical_not(m1)).mean(axis=0).reshape(len(x), len(y)) * 2 - 1

    return double_ps_g, double_ps_e, x, y

def average_sort_decay_data(decay_times, normalise_constant=None,):
    dd = {} 
    for dt in decay_times:
        dd[str(dt)] = []
    for n, dt in enumerate(dts):
        dd[str(dt//1000*1000)].append(dg[n])

    d_avg = {}

    for dt in decay_times:
        data = np.array(dd[str(dt)]).mean(axis=0)
        if normalise:
            data/=normalise_constant
        d_avg[str(dt)]=data
    return d_avg

def find_keys_by_values(data_dict, val_to_find): 
    results_array=[]
    for k in data_dict.keys():
        key, val = next(iter(raw_data[k].items()))
        if key == val_to_find:
            results_array.append(raw_data[k][key])
    return np.array(results_array)

def plot_cats(x,y,d_avg):
    rows = 1
   # cols = len(d_avg_key)
    cols = len(d_avg)
    fig, axes = plt.subplots(rows, cols, figsize=(30, 20))
    for j in range(cols):
        axes[j].pcolormesh(x,x, d_avg[str(d_avg_key[j])] , cmap="seismic", shading = 'auto', vmax=1, vmin=-1)
        axes[j].set_aspect("equal")
        axes[j].set_title(str(d_avg_key[j]))
        
def plot_single_cat(x,y,d_avg):
    rows = 1
    cols = 1
    smallplot_halfcol_figs_square()
    fig, axes = plt.subplots(rows, cols)
    axes.pcolormesh(x*3, x*3, d_avg, cmap="seismic", shading = 'auto', vmax=1, vmin=-1)
    axes.set_aspect("equal")
    return fig