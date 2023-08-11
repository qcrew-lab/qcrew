import numpy as np
import matplotlib.pyplot as plt
import h5py

# fit = fit_all()

filepath = "D://data//YABBAv4//20230811//"

filenames = [
    "215507_YABBA_QML_number_split_spec_vacuum.h5",
    "215603_YABBA_QML_number_split_spec_grape_fock1_pulse.h5",
    "215700_YABBA_QML_number_split_spec_grape_fock2_pulse.h5",
    "215754_YABBA_QML_number_split_spec_grape_fock3_pulse.h5",
    "215850_YABBA_QML_number_split_spec_grape_fock4_pulse.h5",
    "215946_YABBA_QML_number_split_spec_grape_fock5_pulse.h5",
    "220042_YABBA_QML_number_split_spec_grape_fock6_pulse.h5",
    "220136_YABBA_QML_number_split_spec_grape_fock7_pulse.h5",
    "220247_YABBA_QML_number_split_spec_grape_fock8_pulse.h5",
]

fock = [0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8]
parities = []



for file in filenames:
    h5 = h5py.File(filepath+file, "r")
    # keys = list(h5.keys())
    data = h5["data"]
    Pe = np.average(data["state"])
    parities.append(2 * Pe - 1.0)


plt.plot(fock, parities,'o')
plt.ylim(-1,1)
plt.xlabel('Fock state')
plt.ylabel('Parity')
plt.show()