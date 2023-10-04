import h5py
import matplotlib.pyplot as plt
import numpy as np

filepath = r"D:\data\YABBAv4\20230923\161902_YABBA_power_rabi.h5"

file = h5py.File(filepath, "r")
data = file["data"]
I = data["I"][::]
x = data["x"][::]

sweep_points = int(np.shape(x)[0])

ss = True  # SINGLE SHOTS?

threshold = -0.00014956578372339103  # KEEP UP TO DATE

select = True  # DISCARD EXPERIMENTS WHEN QUBIT STARTS IN e?

# When using 1 measurement, the number of rows (vertical) are the repetitions and the number of columns (horizontal) are the sweep points. However, when using 2 measurements everything gets messed up (the two results are next to each other, as if it was two different sweep points). We need to flatten the matrix as a vector, get the even entries (first measurement) and odd entries (second measurement) and reshape back to the original shape: repetitions x sweep_points.

flat_data = I.flatten()

I_first = flat_data[0::2]
I_second = flat_data[1::2]

num_of_reps = int(np.shape(I_first)[0] / sweep_points)

I_first = np.reshape(I_first, (num_of_reps, sweep_points))
I_second = np.reshape(I_second, (num_of_reps, sweep_points))


if ss:
    I_first = [[int(cell) for cell in row] for row in (I_first > threshold)]
    I_second = [[int(cell) for cell in row] for row in (I_second > threshold)]

    if select:  # WIP
        I_first = np.transpose(I_first)
        I_second = np.transpose(I_second)

        for sweep_point, row in enumerate(I_first):
            indices = np.array(row).nonzero()
            avg_first = np.average(np.delete(I_first[sweep_point], indices))
            avg_second = np.average(np.delete(I_second[sweep_point], indices))
            print(avg_first)
            print(avg_second)
            # I_second_filtered.append(list(np.delete(I_second[sweep_point], indices)))

            # I_AVG_first = np.average(I_first_filtered, axis=0)
            # I_AVG_second = np.average(I_second_filtered, axis=0)

    else:
        print("enters else")
        I_AVG_first = np.average(I_first, axis=0)
        I_AVG_second = np.average(I_second, axis=0)


plt.figure(figsize=(12, 8))
if ss:
    plt.ylim(-0.05, 1.05)
plt.plot(I_AVG_first)
plt.plot(I_AVG_second)
plt.show()
