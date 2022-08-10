from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig, LoopbackInterface
import numpy as np
import matplotlib.pyplot as plt
from qm.qua import *

qmm = QuantumMachinesManager()

config = {
    "version": 1,
    
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {
                1: {"offset": +0.0}
            }
        }
    },
    
    "elements": {
        "qe1": {
            "singleInput": {"port": ("con1", 1)},
            "intermediate_frequency": 5e6,
            "operations": {
                "playOp": "constPulse"
            }
        }
    },
    
    "pulses": {
        "constPulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {
                "single": "const_wf"
            }
        }
    },
    
    "waveforms": {
        "const_wf": {
            "type": "constant",
            "sample": 0.2
        }
    }
}

def declare_vars(stream_num=1):
    time_var = declare(int, value = 100)
    amp_var = declare(fixed, value = 0.2)
    stream_array = [declare_stream() for num in range(stream_num)]
    return [time_var, amp_var, stream_array]

def modify_var(addition = 0.3):
    assign(b, b + addition)
    
def qua_function_calls(el):
    play("playOp", el, duration = 300)
    play("playOp"*amp(b), el, duration = 300)

with program() as prog:
    [t, b, c_streams] = declare_vars()
    
    save(b, c_streams[0])
    play("playOp"*amp(b), "qe1", duration = t)
    
    modify_var()
    save(b, c_streams[0])
    play("playOp"*amp(b), "qe1", duration = t)
    
    qua_function_calls("qe1")
    
    with stream_processing():
        c_streams[0].save_all("out_stream")

