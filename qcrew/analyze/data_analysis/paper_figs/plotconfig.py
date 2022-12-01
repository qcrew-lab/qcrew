# Some plotting defaults

import matplotlib as mpl
import matplotlib.cm
import numpy as np


bwr = [(0.0, 0.0, 0.7), (0.1, 0.1, 1.0), (1.0, 1.0, 1.0), (1.0, 0.1, 0.1), (0.7, 0.0, 0.0)]
pcolor_cmap = mpl.colors.LinearSegmentedColormap.from_list('mymap', bwr, gamma=1)


cm = 1.0/2.54  # centimeters in inches

def general_figure():
    mpl.rcParams['figure.figsize'] = [10,8]
    mpl.rcParams['axes.linewidth'] = 1
    mpl.rcParams['xtick.major.size'] = 1.5
    mpl.rcParams['ytick.major.size'] = 1.5
    mpl.rcParams['xtick.minor.size'] = 1
    mpl.rcParams['ytick.minor.size'] = 1
    mpl.rcParams['legend.frameon'] = True
    mpl.rcParams['legend.loc'] = 'best'
    mpl.rcParams['xtick.major.width'] = 1.5
    mpl.rcParams['ytick.major.width'] = 1.5
    mpl.rcParams['xtick.minor.width'] = 0.8
    mpl.rcParams['ytick.minor.width'] = 0.8
    mpl.rcParams['font.sans-serif'] ='Arial'
    mpl.rcParams['font.size'] = 20
    mpl.rcParams['axes.labelsize']= 20
    mpl.rcParams['legend.fontsize'] = 20


def smallplot_halfcol_figs(): 
    ## for double column papers, half-column figure can take up to 8.6cm in width as a whole. 
    mpl.rcParams['figure.figsize'] = [1*cm, 3.8*cm]#[3.2*cm, 1.6*cm]
    mpl.rcParams['axes.linewidth'] = 1
    mpl.rcParams['xtick.major.size'] = 2
    mpl.rcParams['ytick.major.size'] = 2
    mpl.rcParams['xtick.minor.size'] = 2
    mpl.rcParams['ytick.minor.size'] = 2
    mpl.rcParams['xtick.major.width'] = 1
    mpl.rcParams['ytick.major.width'] = 1
    mpl.rcParams['xtick.major.top'] = False
    mpl.rcParams['xtick.major.bottom'] = True
    mpl.rcParams['ytick.labelsize'] = 10
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['xtick.labelbottom'] = False
    mpl.rcParams['xtick.direction'] = 'in'
    mpl.rcParams['ytick.labelleft'] = False
    mpl.rcParams['ytick.direction'] = 'in'

def smallplot_halfcol_figs_square(): 
    ## for double column papers, half-column figure can take up to 8.6cm in width as a whole. 
    mpl.rcParams['figure.figsize'] = [3*cm, 3*cm]
    mpl.rcParams['axes.linewidth'] = 1
    mpl.rcParams['xtick.major.size'] = 2
    mpl.rcParams['ytick.major.size'] = 2
    mpl.rcParams['xtick.minor.size'] = 2
    mpl.rcParams['ytick.minor.size'] = 2
    mpl.rcParams['xtick.major.width'] = 1
    mpl.rcParams['ytick.major.width'] = 1
    mpl.rcParams['xtick.major.top'] = False
    mpl.rcParams['xtick.major.bottom'] = True
    mpl.rcParams['ytick.major.left'] = True
    mpl.rcParams['ytick.labelsize'] = 10
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['xtick.labelbottom'] = False
    mpl.rcParams['xtick.direction'] = 'in'
    mpl.rcParams['ytick.labelleft'] = False
    mpl.rcParams['ytick.direction'] = 'in'
    
def find_vmax(data):
    z_min = data.flatten().min()
    z_max = data.flatten().max()
    vmax = max(abs(z_min), abs(z_max))
    return vmax


colours_one  = [
     [0.05, 0.06, 0.08],
     [0.75, 0.  , 0.11],
     [0.44, 0.  , 0.51],
     [0.49, 0.81, 0.64],
     [0.77, 0.72, 0.57],
     [1.  , 0.42, 0.02],
     [0.59, 0.  , 0.25],
     [0.18, 0.38, 0.42],
     [0.75, 0.57, 0.11],
     [0.01, 0.45, 0.  ],
     [0.32, 0.29, 0.13],
     [0.29, 0.  , 0.  ],
     [0.98, 0.52, 0.53],
]
 
colours_two = [
  #  [0.90, 0.92, 0.92],
    [0.84, 0.17, 0.15],
    [0.10, 0.09, 0.09],
    [0.12, 0.19, 0.44],
    [0.47, 0.75, 0.65],
    [0.47, 0.03, 0.27],
    [0.5,  0.53, 0.53],
    [0.58, 0.3,  0.11],
    [0.89, 0.45, 0.55],
    [0.0,  0.44, 0.21],
    [0.0,  0.53, 0.75],
    [0.98, 0.78, 0.12],
]

def test_colours(c_list):
    xs = np.linspace(0, 1, 11)
    general_figure()
    for kk in range(len(xs)):
        plt.plot(xs, 2*xs[kk]*np.sin(xs), lw=4, color=c_list[kk], label = str(clist[kk]))
    plt.legend()