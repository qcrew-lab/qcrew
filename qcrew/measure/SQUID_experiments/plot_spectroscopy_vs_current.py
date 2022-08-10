import h5py
import matplotlib.pyplot as plt
import numpy as np
from os import listdir


def read_results(filepath):
    data = h5py.File(filepath, "r")["data"]
    freqs_total = np.array([])  # total list of frequencies LO+IF
    spec_per_current = {}  # one spectroscopy data per current bias value
<<<<<<< HEAD
    for indx in range(len(data.keys())):
        experiment = "exp_" + str(indx +1)
=======

    for experiment in data.keys():
>>>>>>> de6211f2e29d356d80f941276b1d45a86e3df7be
        # if experiment == "exp_99":
        #    continue
        # Each experiment has one qubit_lo and current bias associated with it
        current = float(np.array(data[experiment]["current"]))
        qubit_lo = float(np.array(data[experiment]["qubit_LO"]))
        z_avg = np.array(data[experiment]["Z_AVG"])
        freqs = np.array(data[experiment]["freqs"])  # spectroscopy frequency lo+if
        if current not in spec_per_current.keys():
            spec_per_current[current] = {"Z_AVG": tuple(), "freqs": tuple()}
        spec_per_current[current]["Z_AVG"] += (z_avg,)
        spec_per_current[current]["freqs"] += (freqs,)
    # Get freqs_total
<<<<<<< HEAD
    for current in spec_per_current.keys():
=======
    current_list = list(spec_per_current.keys())
    current_list.sort()
    for current in current_list:
>>>>>>> de6211f2e29d356d80f941276b1d45a86e3df7be
        freqs = np.concatenate(spec_per_current[current]["freqs"])
        if len(freqs) > len(freqs_total):
            # update freqs_total
            freqs_total = freqs
    # build z_matrix
    z_matrix = []
    currents_total = []
<<<<<<< HEAD
    for current in spec_per_current.keys():
=======
    for current in current_list:
>>>>>>> de6211f2e29d356d80f941276b1d45a86e3df7be
        freqs = np.concatenate(spec_per_current[current]["freqs"])
        if len(freqs) == len(freqs_total):
            z_avg = np.concatenate(spec_per_current[current]["Z_AVG"])
            z_matrix.append(z_avg)
            currents_total.append(current)
        else:
            # spectroscopy was unfinished; disregard data for this current bias
            print(
                "Spec for current value of %.3fmA was not concluded. Discarding data."
                % (current * 1e3)
            )
            continue
    return freqs_total, currents_total, np.array(z_matrix)


<<<<<<< HEAD
filepath_list = "C:/Users/qcrew/Desktop/qcrew/data/jonny/20220412/172914_jonny_qubit_spec_current_sweep.h5"  # 234732_cc2_qubit_spec_current_sweep.h5"#
=======
filepath_list = "C:/Users/qcrew/Desktop/qcrew/data/cc1_nusquid/20220511/165834_cc1_qubit_spec_current_sweep.h5"  # 234732_cc2_qubit_spec_current_sweep.h5"#
>>>>>>> de6211f2e29d356d80f941276b1d45a86e3df7be
freqs, currents_1, z_matrix_1 = read_results(filepath_list)

# currents = np.concatenate((np.array(currents_1), currents_2, currents_3), axis=0)
# z_matrix = np.concatenate((z_matrix_1, z_matrix_2, z_matrix_3), axis=0)

fig, ax = plt.subplots()
ax.pcolormesh(currents_1, freqs, -z_matrix_1.T, cmap="Blues")

# filename = (
#    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220317/current_sweep2.npz"
# )
# np.savez(filename, z_signal=z_matrix_1, x_currents=currents_1, y_frequencies=freqs)
