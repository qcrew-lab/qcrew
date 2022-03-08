import h5py
import matplotlib.pyplot as plt
import numpy as np
from os import listdir

# filepath = (
#    "C:/Users/qcrew/Desktop/qcrew/data/cc2_transmon/20220204/143302_cc2_qubit_spec.h5"
# )

data_folders = [
    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220304/",
    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220305/",
    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220306/",
    "C:/Users/qcrew/Desktop/qcrew/data/cc2_deltaSQUID/20220307/",
]
file_list = []
for i in range(len(data_folders)):
    file_list += ["%d_" % (i + 4) + s for s in listdir(data_folders[i])]

# get only relevant experiments
first_file = "4_155832_cc2_rr_spec.h5"
first_index = file_list.index(first_file)
last_file = "7_073441_cc2_qubit_spec.h5"
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
qubit_lo_sweep = list(np.arange(qubit_lo_start, qubit_lo_stop, qubit_lo_step))

sweep_params = []
for current in current_sweep:
    for qubit_lo in qubit_lo_sweep:
        sweep_params.append((current, qubit_lo))

i = 0
Z_matrix = []
for current in current_sweep:

    Z_row = []

    for qubit_lo in qubit_lo_sweep:
        if i < len(file_list):
            print(sweep_params[i][1])
            file_name = file_list[i]
            file_name = data_folders[int(file_name.split("_")[0]) - 4] + "_".join(
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

Z_matrix = np.array(Z_matrix)
print(Z_matrix)
print(Z_matrix.shape)
np.isnan(Z_matrix)
fig, ax = plt.subplots()
X, Y = np.meshgrid(*(current_sweep[:16], freqs_list))
ax.pcolormesh(X, Y, Z_matrix.T)
plt.show()
# print(listdir(data_folder_1))


"""
currents = ["-0.10mA", "-0.05mA", "0.00mA", "0.05mA", "0.10mA", "0.15mA"]

plt.figure(figsize=(12, 8))
for i, current in enumerate(currents):
    file = h5py.File(filepaths[i], "r")
    data = file["data"]
    z_avg = data["Z_AVG"]
    x = data["x"]
    plt.plot(np.array(x)[110:], np.array(z_avg)[110:], label=current)

plt.ylabel("Signal level (a.u.)")
plt.xlabel("IF frequency of qubit pulse (Hz)")
plt.title("Qubit spectroscopy as a function of the current bias")
plt.legend()
plt.show()
"""
