import numpy as np

def func(xs, ys, x0, f0, ofs0,ofs1, amp, t0, alpha):

    xv, yv = np.meshgrid(xs, ys, sparse=False, indexing='xy')
    return ofs0+f0**2/(((xv.T-x0)/1e3)**2+f0**2) * (amp*np.sin(2*np.pi*(f0**2+((xv.T-x0)/1e3)**2)**alpha*(yv.T-t0))+ofs1)

def guess(xs, ys, zs):

    zx = np.sum(zs, axis=0)
    zy = np.sum(zs, axis=1)
    
    idx_max = np.argmax(zy)
    idx_min = np.argmin(zy)
    x0 = xs[idx_max]
    ofs0 = np.min(zs[idx_min,:])
        
    fs = np.fft.rfftfreq(len(xs), ys[1] - ys[0])
    fft = np.fft.rfft(zx - np.mean(zx))[1:]
    idx = np.argmax(abs(fft))+1
    f0 = fs[idx]/2
    ofs1 = np.mean(zs[idx_max,:]-ofs0)
    amp = np.std(zs[idx_max,:] - np.mean(zs[idx_max,:]))*2**0.5
    t0 = -np.angle(fft[idx])*f0*1e3
    alpha = 0.5

    return {
        'alpha': alpha, #(x0, np.min(xs), np.max(xs)),
        'x0': x0, #(x0, np.min(xs), np.max(xs)),
        'f0': f0, #(f0, fs[0], fs[-1]),
        'ofs0': ofs0, #(ofs, np.min(ys), np.max(ys)),
        'ofs1': ofs1, #(ofs, np.min(ys), np.max(ys)),
        'amp': amp, #(amp, 0, np.max(ys) - np.min(ys)),
        't0': t0, #(phi, -2*np.pi, 2*np.pi),
    }



    
 #   general_figure()
 #   plt.figure()
 #   plt.pcolormesh(xv, yv, (ofs0+f0**2/(((xv.T-x0)/1e3)**2+f0**2) * (amp*np.sin(2*np.pi*(f0**2+((xv.T-x0)/1e3)**2)**0.5*(yv.T-t0))+ofs1)).T, cmap = pcolor_cmap,vmin=0, vmax=1)    