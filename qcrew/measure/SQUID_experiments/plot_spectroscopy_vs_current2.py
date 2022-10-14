import h5py
import matplotlib.pyplot as plt
import numpy as np
from os import listdir


def read_results(filepath):
    data = h5py.File(filepath, "r")["data"]
    freqs_total = np.array([])  # total list of frequencies LO+IF
    spec_per_current = {}  # one spectroscopy data per current bias value

    data_ordered = []
    for i in range(len(data.keys())):
        data_ordered.append(data["exp_%d" % (i + 1)])

    for i in range(len(data_ordered)):
        # Each experiment has one qubit_lo and current bias associated with it
        current = float(np.array(data_ordered[i]["current"]))
        qubit_lo = float(np.array(data_ordered[i]["qubit_LO"]))
        z_avg = np.array(data_ordered[i]["Z_AVG"])
        freqs = np.array(data_ordered[i]["freqs"])  # spectroscopy frequency lo+if
        if current not in spec_per_current.keys():
            spec_per_current[current] = {"Z_AVG": tuple(), "freqs": tuple()}
        spec_per_current[current]["Z_AVG"] += (z_avg,)
        spec_per_current[current]["freqs"] += (freqs,)
    # Get freqs_total
    current_list = list(spec_per_current.keys())
    current_list.sort()
    for current in current_list:
        freqs = np.concatenate(spec_per_current[current]["freqs"])
        if len(freqs) > len(freqs_total):
            # update freqs_total
            freqs_total = freqs
    # build z_matrix
    z_matrix = []
    currents_total = []
    for current in current_list:
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


# filepath_list = "C:/Users/qcrew/Desktop/qcrew/data/jonny-hose/20220919/172448_jonny_qubit_spec_current_sweep.h5"  # 234732_cc2_qubit_spec_current_sweep.h5"#
# filepath_list = "C:/Users/qcrew/Desktop/qcrew/data/jonny-hose/20220921/152812_jonny_qubit_spec_current_sweep.h5"

filepath_list1 = "C:/Users/qcrew/Desktop/qcrew/data/jonny-hose/20220921/192051_jonny_qubit_spec_current_sweep.h5"
filepath_list2 = "C:/Users/qcrew/Desktop/qcrew/data/jonny-hose/20220922/135545_jonny_qubit_spec_current_sweep.h5"
freqs, currents_1, z_matrix_1 = read_results(filepath_list1)
freqs, currents_2, z_matrix_2 = read_results(filepath_list2)

# print(z_matrix_1)
print(z_matrix_1.shape)
print(z_matrix_2.shape)
print(len(currents_1))
print(len(currents_2))
print(freqs)
currents = np.concatenate((currents_1[:25], currents_2))
fig, ax = plt.subplots(nrows=2, figsize=(8, 6))
# plt.plot(freqs)
z_matrix_1 = z_matrix_1[:25, :]
Z_1 = z_matrix_1.T - np.mean(z_matrix_1)
Z_2 = z_matrix_2.T - np.mean(z_matrix_2)
Z = np.abs(np.concatenate((z_matrix_1.T, z_matrix_2.T), axis=1))
print(Z.shape)
ax.pcolormesh(
    currents * 1e3,
    freqs * 1e-9,
    Z,
    vmax=0.0003,
    vmin=0.5e-4,
    cmap="magma_r",
)
ax.set_xlabel("Current bias (mA)")
ax.set_ylabel("Frequency (GHz)")
plt.savefig("spectroscopy_J-A.pdf")
# np.savez(z_matrix_1)
# filename = (
#    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220317/current_sweep2.npz"
# )
# np.savez(filename, z_signal=z_matrix_1, x_currents=currents_1, y_frequencies=freqs)
