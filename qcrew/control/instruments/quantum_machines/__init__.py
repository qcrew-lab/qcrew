""" """

CONTROLLER_NAME = "con1"
CONTROLLER_TYPE = "opx1"
AO_MIN, AO_MAX = 1, 10  # analog output port number bounds [min, max]
AI_MIN, AI_MAX = 1, 2  # analog input port number bounds [min, max]
V_MIN, V_MAX = -0.5, 0.5  # voltage bounds (min, max)
MCM_MIN, MCM_MAX = -2.0, 2 - 2 ** -16  # mixer correction matrix value bounds (min, max)
DEFAULT_AMP = 0.25  # in V
CLOCK_CYCLE = 4  # in ns
MIN_PULSE_LEN = 16  # in ns
RO_DIGITAL_MARKER, RO_DIGITAL_SAMPLES = "ON", [(1, 0)]  # readout pulse digital waveform
