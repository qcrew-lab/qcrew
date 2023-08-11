import numpy as np
import matplotlib.pyplot as plt

# t = np.linspace(0, 2.1, 2101)

# chi = 1.5

# n = 5**2

# pe = 1 / 2 * (1 + np.exp(n * np.cos(chi * t) - n) * np.cos(n * np.sin(chi * t)))

# plt.plot(t, -0.008*pe+0.006)




alpha = [0.5, 1.0, 1.5, 2.0]
n = [i**2 for i in alpha]

peaks = [24000, 22500, 20000, 16000]

freqs = [1/(peak*4)*(10**6) for peak in peaks] # kHz

detuning = 10 # kHz

coef = np.polyfit(n,freqs,1)
poly1d_fn = np.poly1d(coef) 

print(coef)

plt.xlabel("photon number")
plt.ylabel("Oscil. frequency (kHz)")
plt.scatter(n, freqs, color=['b','r','g','y'])
plt.plot (n,poly1d_fn(n), '--k')
plt.text(2, 10.5, "slope = "+ str(coef[0]))
plt.text(2, 10, "offset = "+ str(coef[1]))
plt.show()




