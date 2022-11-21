""" simple script to create a custom pulse and save as npz file """

import numpy as np
import matplotlib.pyplot as plt

pulse_name = "tanh2"
save_path = f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/custom_pulses/{pulse_name}.npz"

pulse_len = 251
xs = np.linspace(0, 1, pulse_len)
i_arr = -0.5 * np.tanh(10 * (xs - 0.5))
i_arr[125:] = 0
i_arr = 0.5 * np.exp(-((xs - 0.5) ** 2))
q_arr = np.zeros(pulse_len)
pulse_arr = i_arr + 1j * q_arr
np.savez(save_path, pulse=pulse_arr)

plt.clf()
plt.plot(xs, i_arr)
plt.plot(xs, i_arr)
plt.show()
