#%%
import h5py
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

filepath = "D:/data/YABBAv4/20230508/123520_YABBA_wigner_function_2D_grape.h5"
file = h5py.File(filepath, "r")
data = file["data"]
z = np.array(data["I"])
z_ave = np.mean(z, axis=0)#taking the average
res = int(np.sqrt(z.shape[1]))#resolution for wigner res*res
z_m = z_ave.reshape(res,res)#reshape

z_m = -1*z_m#z flip
z_m = z_m-1.8e-4#offset
z_m = 5321.0875166984415*z_m#z scaling
Mexp = z_m#the data to plot

fig = plt.figure(figsize = (5,5))
ax1 = fig.add_subplot(111, projection="3d", elev=90, azim=-90)
#the grid
beta_max = 2
beta_re = np.linspace(-beta_max,beta_max,res)
beta_im = np.linspace(-beta_max,beta_max,res)
# beta_im = np.flip(beta_im)
Y,X = np.meshgrid(beta_re, beta_im)
surf = ax1.plot_surface(X, Y, Mexp, cmap=cm.coolwarm, rstride=1, cstride=1, linewidth=0, antialiased=False)#, vmin = -1, vmax = 1)
fig.colorbar(surf, shrink=0.5, aspect=5)
ax1.set_xlabel('Re'+r'$(\beta)$')
ax1.set_ylabel('Im'+r'$(\beta)$')

plt.show()

print(np.max(Mexp))
print(np.min(Mexp))