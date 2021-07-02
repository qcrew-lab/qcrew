""" Check drag pulse waveforms with the QM simulator """
import numpy as np
import matplotlib.pyplot as plt
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import program, play, amp
from qm import SimulationConfig

def gaussian_fn(maximum: float, sigma: float, chop: int):
    length = int(chop * sigma)
    mu = int(np.floor(length / 2))
    t = np.linspace(0, length - 1, length)
    gaussian = maximum * np.exp(-((t - mu) ** 2) / (2 * sigma ** 2))
    return [float(x) for x in gaussian]

def gaussian_derivative_fn(gauss_A: float, drag: float, sigma: float, chop: int):
    length = int(chop * sigma)
    mu = int(np.floor(length / 2))
    t = np.linspace(0, length - 1, length)
    gaussian = gauss_A * np.exp(-((t - mu) ** 2) / (2 * sigma ** 2))
    gaussian_derivative = drag * gaussian * (t - mu) / (sigma ** 2)
    return gaussian_derivative

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {
                1: {"offset": 0.0},
                2: {"offset": 0.0},
            },
        },
    },
    "elements": {
        "qubit": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": int(5e9),
                "mixer": "mixer_qubit",
            },
            "intermediate_frequency": int(-50e6),
            "operations": {
                "drag1": "drag1",
                "drag2": "drag2",
            },
        },
    },
    "pulses": {
        "drag1": {
            "operation": "control",
            "length": 700,
            "waveforms": {"I": "gauss_wf", "Q": "dgauss1_wf"}
        },
        "drag2": {
            "operation": "control",
            "length": 700,
            "waveforms": {"I": "gauss_wf", "Q": "dgauss2_wf"}
        },
    },
    "waveforms": {
        "zero_wf": {
            "type": "constant",
            "sample": 0.0,
        },
        "gauss_wf": {
            "type": "arbitrary",
            "samples": gaussian_fn(0.2 * 1.9164, 175, 4),
        },
        "dgauss1_wf": {
            "type": "arbitrary",
            "samples": gaussian_derivative_fn(0.2 * 1.9164, 288.5, 175, 4),
        },
        "dgauss2_wf": {
            "type": "arbitrary",
            "samples": gaussian_derivative_fn(0.2 * 1.9164, 13.271, 175, 4),
        },
    },
    "mixers": {
        "mixer_qubit": [
            {
                "intermediate_frequency": int(-50e6),
                "lo_frequency": int(5e9),
                "correction": (1.0, 0.0, 0.0, 1.0),
            },
        ],
    },
}

qmm = QuantumMachinesManager()

with program() as test1:
    play("drag1" * amp(1.0, 0.0, 0.0, 0.046), "qubit")

with program() as test2:
    play("drag2", "qubit")

sim_config = SimulationConfig(duration=250, include_analog_waveforms=True)

job1 = qmm.simulate(config, test1, sim_config)
samples1 = job1.get_simulated_samples()
i_samples1, q_samples1 = samples1.con1.analog["1"], samples1.con1.analog["2"]

job2 = qmm.simulate(config, test2, sim_config)
samples2 = job2.get_simulated_samples()
i_samples2, q_samples2 = samples2.con1.analog["1"], samples2.con1.analog["2"]

i_diff = i_samples1 - i_samples2
q_diff = q_samples1 - q_samples2

fig = plt.figure(figsize=(12, 8))
ax1, ax2, ax3 = plt.subplot(311), plt.subplot(312), plt.subplot(313)

ax1.set_title("DRAG pulse scaled with amp matrix [1, 0, 0, beta] in QUA loop")
ax2.set_title("DRAG pulse with Gaussian derivative waveform amps scaled in QM config")
ax3.set_title("Difference between the OPX analog outputs for both DRAG pulses")

ax1.plot(i_samples1, label="I: AO1", color="blue")
ax1.plot(q_samples1, label="Q: AO2", color="orange")

ax2.plot(i_samples2, label="I: AO1", color="blue")
ax2.plot(q_samples2, label="Q: AO2", color="orange")

ax3.plot(i_diff, label="Diff I: AO1", color="blue")
ax3.plot(q_diff, label="Diff Q: AO2", color="orange")

ax1.legend()
ax2.legend()
ax3.legend()

plt.xlabel("Time [ns]")
plt.ylabel("Signal [V]")
plt.show()
