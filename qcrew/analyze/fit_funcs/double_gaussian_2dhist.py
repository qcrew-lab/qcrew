import numpy as np

def func(xs, ys, x0, y0, x1, y1, a0, a1, ofs, sigma=2):
    '''
    Gaussian defined by it's area <area>, sigma <s>, position <x0> and
    y-offset <ofs>.
    '''
    r0 = (xs - x0)**2 + (ys - y0)**2
    r1 = (xs - x1)**2 + (ys - y1)**2
    zs = ofs + a0*np.exp(-0.5 * r0 / sigma**2) + a1*np.exp(-0.5 * r1 / sigma**2)
    return zs

def guess(xs, ys, zs):
    zofs = np.mean([zs[0,:], zs[-1,:], zs[:,0], zs[:,-1]])
    zs = zs - zofs

    # Locate first max
    maxidx0 = np.argmax(np.abs(zs))
    x0 = xs.flatten()[maxidx0]
    y0 = ys.flatten()[maxidx0]
    a0 = zs.flatten()[maxidx0]

    # Other estimates
    dmin = (np.max(xs) - np.min(xs)) / 8
    mask = ((xs - xs.flatten()[maxidx0])**2 + (ys - ys.flatten()[maxidx0])**2) > dmin**2
    sigma = np.abs(dmin)

    # Locate second max
    maxidx1 = np.argmax(np.abs(zs[mask]))
    x1 = xs[mask].flatten()[maxidx1]
    y1 = ys[mask].flatten()[maxidx1]
    a1 = zs[mask].flatten()[maxidx1]

    return dict(
        ofs=zofs,
        x0=x0, y0=y0,
        x1=x1, y1=y1,
        a0=a0, a1=a1,
        sigma=sigma,
    )
