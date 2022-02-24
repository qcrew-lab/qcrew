from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import qua
import time

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {
                1: {"offset": +0.0},  # I
                2: {"offset": +0.0},  # Q
            },
            "digital_outputs": {
                1: {},
            },
        }
    },
    "elements": {
        "qubit": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "mixer": "mixer1",
                "lo_frequency": 5e9,
            },
            "intermediate_frequency": -50e6,
            "digitalInputs": {
                "input_switch": {
                    "port": ("con1", 1),
                    "delay": 144,
                    "buffer": 0,
                },
            },
            "operations": {"pulse1": "pulse1"},
        },
    },
    "pulses": {
        "pulse1": {
            "operation": "control",
            "length": 1000,
            "waveforms": {
                "I": "wf_I",
                "Q": "wf_Q",
            },
            "digital_marker": "digital_waveform_high",
        },
    },
    "waveforms": {
        "wf_I": {"type": "constant", "sample": 0.2},
        "wf_Q": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "digital_waveform_high": {"samples": [(1, 0)]},
    },
    "mixers": {
        "mixer1": [
            {
                "intermediate_frequency": -50e6,
                "lo_frequency": 5e9,
                "correction": [1, 0, 0, 1],
            }
        ],
    },
}

with qua.program() as play_constant_pulse:
    x = qua.declare(int)
    with qua.for_(x, 0, x<=10, x+1):
        qua.play("pulse1", "qubit")

qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
job = qm.execute(play_constant_pulse)
job.result_handles.wait_for_all_values()
print("done")
#time.sleep(60)
#job.halt()
