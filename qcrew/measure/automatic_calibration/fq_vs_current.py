import numpy as np
import matplotlib.pyplot as plt

# Define the first and second arrays
qubit_LO = 5.766594250e9
currents = np.array(
    [
        2.670e-3,
        2.660e-3,
        2.650e-3,
        2.640e-3,
        2.630e-3,
        2.620e-3,
        2.610e-3,
        2.600e-3,
        2.590e-3,
        2.580e-3,
    ]
)
qubit_IFs = np.array(
    [-61.72, -59.90, -58.00, -55.84, -54.24, -51.94, -49.96, -48.20, -46.48, -44.73]
)
qubit_fs = qubit_IFs * 1e6

# Perform linear fit using numpy.polyfit
slope, intercept = np.polyfit(currents, qubit_fs, 1)
fit_line = slope * currents + intercept

# Create a scatter plot
plt.figure(figsize=(6, 5))
plt.scatter(currents, qubit_fs, color="blue", marker="o", label="Data Points")
plt.plot(currents, fit_line, color="red", label=f"Linear Fit, slope = {slope/1e9}e9")

# Add labels and title
plt.ylabel("Qubit frequency (MHz, LO = 5.766594250e9)")
plt.xlabel("Current (mA)")
# plt.title("Scatter Plot of Two Arrays")
plt.legend()

# Display the plot
plt.grid()
plt.show()
