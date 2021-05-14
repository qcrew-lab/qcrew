""" """
from dataclasses import dataclass, field

from qcrew.analysis.funclib import func_map
from qcrew.helpers.yamlizer import Yamlable

class Pulse(Yamlable):
    pass

class ControlPulse(Pulse):
    pass

class MeasurementPulse(Pulse):
    pass

class Waveform(Yamlable):
    pass

class ConstantWaveform(Waveform):
    pass

class ArbitraryWaveform(Waveform):
    pass

def make_pulse():
    pass

# ------------------------ Archetypical pulses and waveforms --------------------------

#DEFAULT_CW_PULSE
#DEFAULT_GAUSSIAN_PULSE
#DEFAULT_READOUT_PULSE
#ZERO_WAVEFORM
#DEFAULT_CONSTANT_WAVEFORM
#DEFAULT_GAUSS_WAVEFORM
