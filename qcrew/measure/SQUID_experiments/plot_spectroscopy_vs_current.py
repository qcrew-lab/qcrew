import h5py
import matplotlib.pyplot as plt
import numpy as np
from os import listdir


def read_results(filepath):
    data = h5py.File(filepath, "r")["data"]
    freqs_total = np.array([])  # total list of frequencies LO+IF
    spec_per_current = {}  # one spectroscopy data per current bias value
    for experiment in data.keys():
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
    for current in spec_per_current.keys():
        freqs = np.concatenate(spec_per_current[current]["freqs"])
        if len(freqs) > len(freqs_total):
            # update freqs_total
            freqs_total = freqs
    # build z_matrix
    z_matrix = []
    currents_total = []
    for current in spec_per_current.keys():
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


data_folders = [
    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220309/",
]
file_list = []
for i in range(len(data_folders)):
    file_list += ["%d_" % (i + 9) + s for s in listdir(data_folders[i])]

# get only relevant experiments
first_file = "9_154827_cc2_rr_spec.h5"
first_index = file_list.index(first_file)
last_file = "9_163312_cc2_qubit_spec.h5"
last_index = file_list.index(last_file)
file_list = file_list[first_index : last_index + 1]

# keep only qubit spec experiments
for f in file_list:
    print(f)
file_list = [x for x in file_list if "qubit_spec" in x]

# pair up each file to a current and a qubit_lo
current_start = 10e-3
current_stop = -10.1e-3
current_step = -0.5e-3
current_sweep = np.arange(current_start, current_stop, current_step)

qubit_lo_start = 5.42733e9
qubit_lo_stop = 4e9
qubit_lo_step = -200e6
qubit_lo_sweep = np.arange(qubit_lo_start, qubit_lo_stop, qubit_lo_step)

sweep_params = []
for current in current_sweep:
    for qubit_lo in qubit_lo_sweep:
        sweep_params.append((current, qubit_lo))

i = 0
Z_matrix = []
freqs_list = []
for current in current_sweep:
    Z_row = []
    for qubit_lo in qubit_lo_sweep:
        if i < len(file_list):
            print(sweep_params[i][1])
            file_name = file_list[i]
            file_name = data_folders[int(file_name.split("_")[0]) - 9] + "_".join(
                file_name.split("_")[1:]
            )
            file = h5py.File(file_name, "r")
            data = file["data"]
            z_avg = np.array(data["Z_AVG"])
            ## Correct floor of z_avg
            z_avg -= np.average(z_avg)
            z_avg = list(z_avg)
            z_avg.reverse()
            floor = np.average(z_avg)
            freqs = np.array(data["x"]) + sweep_params[i][1]
            freqs = list(freqs)
            freqs.reverse()
            freqs_list += freqs
            Z_row += z_avg
            i += 1
            print(i, file_name)
    if i < len(file_list):
        freqs_list = []
        Z_matrix.append(np.array(Z_row))
z_matrix_2 = np.array(Z_matrix)
currents_2 = current_sweep[:40]


filepath_list = "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220317/154616_cc2_qubit_spec_current_sweep.h5"  # 234732_cc2_qubit_spec_current_sweep.h5"#
freqs, currents_1, z_matrix_1 = read_results(filepath_list)

# currents = np.concatenate((np.array(currents_1), currents_2, currents_3), axis=0)
# z_matrix = np.concatenate((z_matrix_1, z_matrix_2, z_matrix_3), axis=0)

fig, ax = plt.subplots()
ax.pcolormesh(currents_1, freqs, -z_matrix_1.T, cmap="Blues")

# filename = (
#    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220317/current_sweep2.npz"
# )
# np.savez(filename, z_signal=z_matrix_1, x_currents=currents_1, y_frequencies=freqs)
