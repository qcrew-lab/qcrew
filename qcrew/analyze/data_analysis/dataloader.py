import h5py
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import math
import os


def load_triple_mask_decay(path: str, file_end:str, plot: bool = True):
    
    # load all files
    fps = []
    fp = [path + f for f in os.listdir(path) if f.endswith(file_end)]
    fps = np.concatenate([fp[:]])
    
    dg = []
    de = []
    dts = []
    for kk in range(len(fps)):
#         fname = d + files[kk]
        df = h5py.File(fps[kk], "r")
        data = df["data"]
        data_i = data["I"][:]
        x = data["x"][:, 0, 0]
        y = data["y"][0, :, 0]
        dt = df.attrs['decay_time']
        thresh = -6.687025253601604e-06
#         ss_data = np.where(data_i < thresh, 1, 0)
#         thresh_1 = 6.30337300715842e-05
        raw_m0 = data_i[:, 0::3]
        raw_m1 = data_i[:, 1::3] 
        raw_m2 = data_i[:, 2::3]
        
        m0 = np.where(raw_m0 < thresh, 1, 0)
        m1 = np.where(raw_m1 < thresh, 1, 0)
        m2 = np.where(raw_m2 < thresh, 1, 0)
        
#         ss_data = np.where(data_i < thresh, 1, 0)
#         m0 = ss_data[:, 0::3]
#         m1 = ss_data[:, 1::3] 
#         m2 = ss_data[:, 2::3]
        m1_g = ma.masked_array(m1, mask=m0)
        m2_g = ma.masked_array(m2, mask=m0)

        ## only care about last two measurements
        proj_g = ma.masked_array(m2, mask=m1).mean(axis=0).reshape(len(x), len(y)) * 2 - 1
        proj_e = ma.masked_array(m2, mask=np.logical_not(m1)).mean(axis=0).reshape(len(x), len(y)) * 2 - 1

        ## condition on the first measurement as well
        double_ps_g = ma.masked_array(m2_g, mask=m1_g).mean(axis=0).reshape(len(x), len(y)) * 2 - 1
        double_ps_e = ma.masked_array(m2_g, mask=np.logical_not(m1_g)).mean(axis=0).reshape(len(x), len(y)) * 2 - 1

        dg.append(double_ps_g)
        de.append(double_ps_e)
        dts.append(dt)
        
    dg = np.array(dg)
    de = np.array(de)
    dts = np.array(dts)
    decay_times = np.unique(dts)
    dd = {}
    for n in range(len(decay_times)):
        dd[str(decay_times[n])] = []

    for n, dt in enumerate(dts):
        dd[str(dt)].append(dg[n])
        
    d_avg = {}
    for n, dt in enumerate(dts): 
        
        d_avg[str(dt)] = np.array(dd[str(dt)]).mean(axis=0)

    rows = 1
    cols = len(decay_times)
    if plot:
        fig, axes = plt.subplots(rows, cols, figsize=(16, 12))
        # for i in range(rows):
        for j in range(cols):
            axes[j].pcolormesh(x, x, d_avg[str(decay_times[j])][:, :], cmap="seismic", shading = 'auto', vmax=1, vmin=-1)
            axes[j].set_aspect("equal")
            axes[j].set_title(str(decay_times[j]))
        #         l += 1      
        plt.show()
    data_array = [d_avg[str(time)] for time in decay_times]
    
    return x, y, data_array, decay_times