import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit, minimize

target_qubit_freq = 5.65e9
qubit_freq_max = 6.43e9
rr_lo = 6.97976e9

path = "C:\\Users\\qcrew\\Desktop\\qcrew\\qcrew\\config\\rrfreq_vs_current\\"
filename = "20230818_144139_rr_current.npz"

# Retrieve and interpolate data
file = np.load(path + filename)
rr_freqs = file["rr_freq"]
currents = file["currents"]
rr_freqs_interpolated = interp1d(currents, rr_freqs, kind="linear")

## Define the cosine function to fit
def cosine_function(x, amplitude, frequency, phase):
    return amplitude * np.cos(2 * np.pi * (frequency * x + phase))


## Perform the curve fitting
periodicity_guess = max(currents) - min(currents)
phase_guess = currents[np.argmax(rr_freqs)] / periodicity_guess
amplitude_guess = (np.max(rr_freqs) - np.min(rr_freqs)) / 2
initial_guess = [amplitude_guess, 1/periodicity_guess, phase_guess]
fit_params, _ = curve_fit(
    cosine_function, currents, rr_freqs - np.average(rr_freqs), p0=initial_guess
)

# Extract the fitted parameters
fitted_amplitude, fitted_freq, fitted_phase = fit_params
current_of_maximum = -fitted_phase/fitted_freq
current_of_minimum = current_of_maximum+1/fitted_freq/2

# Generate the fitted curve
fitted_curve = cosine_function(currents, fitted_amplitude, fitted_freq, fitted_phase) + np.average(
    rr_freqs
)

# Find best stretch of current that covers the whole range of frequencies
# Before proceeding, check if data corresponds to more than a period
if max(currents) - min(currents) > 1/fitted_freq:
    if fitted_phase >= 0:
        tunable_current_min = -fitted_phase/fitted_freq
        tunable_current_max = (0.5 - fitted_phase)/fitted_freq
    if fitted_phase < 0:
        tunable_current_min = (-0.5 - fitted_phase)/fitted_freq
        tunable_current_max = -fitted_phase/fitted_freq

print(f"Estimated Periodicity: {1/fitted_freq*1e3:.3f}mA")
print(f"Current of maximum: {tunable_current_max*1e3:.3f}mA")
print(f"Current of minimum: {tunable_current_min*1e3:.3f}mA")

# Report
currents_grid = np.linspace(min(currents), max(currents), 1000)
fig, ax = plt.subplots(2,1, sharex=True)
ax[0].scatter(currents*1e3, rr_lo + rr_freqs, label = "RR frequency data")
limit_current_grid = np.linspace(tunable_current_min, tunable_current_max, 1000)
ax[0].plot(limit_current_grid*1e3, rr_lo + rr_freqs_interpolated(limit_current_grid), label = "Tunability region")
ax[0].plot(currents*1e3, rr_lo + fitted_curve, linewidth = .6, linestyle = '--', label = "Period fit")
ax[0].set_title(f"Periodicity: {1/fitted_freq*1e3:.3f}mA\nmax: {current_of_maximum*1e3:.3f}mA, min: {current_of_minimum*1e3:.3f}mA")
if qubit_freq_max:
    # Get ideal qubit frequency curve
    qubit_freq_fn = lambda amp: qubit_freq_max*np.sqrt(np.abs(np.cos(np.pi*(fitted_freq*amp + fitted_phase))))
    ax[1].plot(currents_grid*1e3, [qubit_freq_fn(amp) for amp in currents_grid], label = "Ideal qubit frequency curve")
    if target_qubit_freq and target_qubit_freq < qubit_freq_max:
        def cost(x):
            return (target_qubit_freq - qubit_freq_fn(x))**2
        bounds = [(tunable_current_min, tunable_current_max)]
        print(bounds)
        res = minimize(cost, 0, bounds = bounds)
        target_current = res.x[0]
        ax[1].scatter(target_current*1e3, target_qubit_freq, c='r', label = f"Target qubit frequency ({target_current*1e3:.3f}mA)", zorder = 2)
        

ax[0].legend(fontsize="7")
ax[1].legend(fontsize="7")
ax[1].set_xlabel("Current (mA)")
ax[0].grid()
ax[1].grid()
plt.show()