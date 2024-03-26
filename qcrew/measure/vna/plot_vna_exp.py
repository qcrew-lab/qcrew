import h5py
import matplotlib.pyplot as plt
import numpy as np
import os
from tqdm import tqdm
from scipy.signal import find_peaks


def check_for_peaks(y_data, prominence=5):
    """
    Check if there are any significant peaks in the data.
    Returns True if peaks are found, False otherwise.
    """
    peaks, _ = find_peaks(-y_data, prominence=prominence)  # Adjust prominence as needed
    return len(peaks) > 0


# Directory where your data files are stored
directory_path = r"C:\Users\qcrew\Documents\jon\cheddar\data\2024-02-28"

# Directory to save plots
# plots_directory = os.path.join(directory_path, "plots")

# Create the plots directory if it doesn't exist
# if not os.path.exists(plots_directory):
#     os.makedirs(plots_directory)

# List all files in the directory
all_files = os.listdir(directory_path)

# Filter out only HDF5 files
data_files = ["16-59-36_VNA_sweep_6000000000.0_(0, 0)pow_2reps.hdf5"]
# "122024_vnasweep_6e+0GHz.hdf5"
# ]  # [file for file in all_files if file.endswith('.hdf5')]

for filename in tqdm(data_files):
    filepath = os.path.join(directory_path, filename)
    # Open the file
    with h5py.File(filepath, "r") as file:
        data = file["data"]
        s21_mlog = np.array(
            data["s21_imag"][1]
        )  # Assuming you want the first repetition
        s21_phase = np.array(
            data["s21_real"][1]
        )  # Assuming you want the first repetition
        freqs = np.array(data["frequency"])
        print(len(s21_mlog))

        # Plotting the data
        fig, ax = plt.subplots(2, 1, figsize=(16, 8))

        ax[0].plot(freqs, s21_mlog, label="S21 Magnitude (Log)")
        ax[1].plot(freqs, s21_phase, label="S21 Phase")

        ax[0].set_ylabel("Magnitude (dB)")
        ax[1].set_ylabel("Phase (Degrees)")
        ax[1].set_xlabel("Frequency (Hz)")

        # Check for peaks in the magnitude plot
        has_peaks = check_for_peaks(s21_mlog)

        # Set plot titles with file name for clarity
        plot_title = os.path.splitext(filename)[
            0
        ]  # Get the file name without the extension
        if has_peaks:
            plot_title += "_probably_peak"
        ax[0].set_title(f"{plot_title} - S21 Magnitude (Log)")
        ax[1].set_title(f"{plot_title} - S21 Phase")

        plt.tight_layout()
        plt.legend()

        # Save the plot in the plots directory
        # save_path = os.path.join(plots_directory, f"{plot_title}.png")
        plt.plot()
        # plt.close()  # Close the plot to free memory
