""" Python driver for Anritsu VNA MS46522B """

import numpy as np
import pyvisa

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class VNA(Instrument):
    """ """

    HEADER_LEN = 11
    MIN_SWEEP_POINTS = 2
    MAX_SWEEP_POINTS = 20001
    MIN_SWEEP_DELAY = 0
    MAX_SWEEP_DELAY = 100
    MIN_SWEEP_REPETITIONS = 1
    MAX_SWEEP_REPETITIONS = 1024
    MIN_BANDWIDTH = 1
    MAX_BANDWIDTH = 500000
    MIN_TRACES = 1
    MAX_TRACES = 16
    VALID_SWEEP_MODES = ("single", "continuous")
    VALID_S_PARAMETERS = ("s11", "s12", "s21", "s22")
    VALID_TRACE_FORMATS = (
        "imaginar",
        "imag",
        "mlinear",
        "mlin",
        "mlogarithmic",
        "mlog",
        "phase",
        "phas",
        "pwrin",
        "pwri",
        "pwrout",
        "pwro",
        "real",
        "swr",
        "zreal",
        "zcapacitance",
        "zcap",
        "zimaginary",
        "zimag",
        "zinductance",
        "zind",
        "zmagnitude",
        "zmagn",
    )
    DEFAULT_TRACE_LAYOUT = {
        1: "R1C1",
        2: "R1C2",
        **dict.fromkeys([3, 4], "R2C2"),
        **dict.fromkeys([5, 6], "R2C3"),
        **dict.fromkeys([7, 8], "R2C4"),
        9: "R3C3",
        10: "R2C5",
        **dict.fromkeys([11, 12], "R4C3"),
        **dict.fromkeys([13, 14, 15, 16], "R4C4"),
    }

    def __init__(self, id: str, name="") -> None:
        """ """
        super().__init__(id=id, name=name)
        self.handle = None  # updated by connect()
        self.connect()

    def connect(self) -> None:
        """ """
        resource_name = f"TCPIP0::{self.id}::INSTR"
        self.handle = pyvisa.ResourceManager().open_resource(resource_name)
        logger.info(f"Connected to {self}")
        self._initialize()

    def _initialize(self) -> None:
        """ """
        # better to have no timeout for very long sweeps
        self.handle.timeout = None

        self._traces = None

        self.hold()
        self.handle.write(":sense:average:type sweepbysweep")  # enforce default
        self.handle.write(":sweep:type linear")  # for now, only support linear sweeps
        self.handle.write(":sense:sweep:delay:state 1")  # turn per point sweep delay on

    def configure(self, **config) -> None:
        """ """
        self.hold()

        for parameter, value in config.items():
            if hasattr(self, parameter):
                setattr(self, parameter, value)

    def sweep(self, mode="single") -> None:
        """ """
        if mode not in VNA.VALID_SWEEP_MODES:
            return ValueError(f"Invalid {mode = }. Valid = {VNA.VALID_SWEEP_MODES}")

        if mode == "continuous":
            self.handle.write(":sense:hold:function continuous")
        elif mode == "single":
            self.hold()
            self.handle.write(":trigger:single")
            self.handle.write(":display:window:y:auto")  # auto-scale all traces

    def hold(self) -> None:
        """ """
        state = self.handle.query(":sense:hold:function?").rstrip().lower()
        if state != "hold":
            self.handle.write(":sense:hold:function hold")

    def disconnect(self) -> None:
        """ """
        self.handle.close()

    @property
    def data(self) -> dict[str, list[float]]:
        """ """
        self.hold()
        self.handle.write(":display:window:y:auto")  # auto-scale all traces

        data = dict()
        traces = self.traces
        for count, trace_info in enumerate(traces, start=1):
            self.handle.write(f":calculate:parameter{count}:select")
            data_str = self.handle.query(":calculate:data:fdata?")[VNA.HEADER_LEN :]
            s_param, trace_format = trace_info
            key = f"{s_param}_{trace_format}"
            data[key] = np.array([float(value) for value in data_str.split()])
        return data

    @property
    def frequencies(self) -> np.ndarray:
        """ """
        freq_str = self.handle.query(":sense:frequency:data?")[VNA.HEADER_LEN :]
        return np.array([float(freq) for freq in freq_str.split()])

    @property
    def fcenter(self) -> float:
        """ """
        return float(self.handle.query(":sense:frequency:center?"))

    @fcenter.setter
    def fcenter(self, new_fcenter: float) -> None:
        """ """
        self.handle.write(f":sense:frequency:center {new_fcenter}")

    @property
    def fspan(self) -> float:
        """ """
        return float(self.handle.query(":sense:frequency:span?"))

    @fspan.setter
    def fspan(self, new_fspan: float) -> None:
        """ """
        self.handle.write(f":sense:frequency:span {new_fspan}")

    @property
    def fstart(self) -> float:
        """ """
        return float(self.handle.query(":sense:frequency:start?"))

    @fstart.setter
    def fstart(self, new_fstart: float) -> None:
        """ """
        self.handle.write(f":sense:frequency:start {new_fstart}")

    @property
    def fstop(self) -> float:
        """ """
        return float(self.handle.query(":sense:frequency:stop?"))

    @fstop.setter
    def fstop(self, new_fstop: float) -> None:
        """ """
        self.handle.write(f":sense:frequency:stop {new_fstop}")

    @property
    def bandwidth(self) -> float:
        """ """
        return float(self.handle.query(":sense:bandwidth?"))

    @bandwidth.setter
    def bandwidth(self, new_bandwidth: float) -> None:
        """ """
        min_, max_ = VNA.MIN_BANDWIDTH, VNA.MAX_BANDWIDTH
        if not min_ <= new_bandwidth <= max_:
            raise ValueError(f"Bandwidth must be in [{min_}, {max_}]")
        self.handle.write(f":sense:bandwidth {new_bandwidth}")

    @property
    def sweep_delay(self) -> float:
        """ """
        return float(self.handle.query(":sense:sweep:delay?"))

    @sweep_delay.setter
    def sweep_delay(self, new_sweep_delay: float) -> None:
        """ """
        min_, max_ = VNA.MIN_SWEEP_DELAY, VNA.MAX_SWEEP_DELAY
        if not min_ <= new_sweep_delay <= max_:
            raise ValueError(f"Sweep delay must be in [{min_}, {max_}]")
        self.handle.write(f":sense:sweep:delay {new_sweep_delay}")

    @property
    def sweep_points(self) -> int:
        """ """
        return int(self.handle.query(":sense:sweep:point?"))

    @sweep_points.setter
    def sweep_points(self, new_sweep_points: int) -> None:
        """ """
        min_, max_ = VNA.MIN_SWEEP_POINTS, VNA.MAX_SWEEP_POINTS
        if not min_ <= new_sweep_points <= max_:
            raise ValueError(f"Sweep points must be in [{min_}, {max_}]")
        self.handle.write(f":sense:sweep:point {new_sweep_points}")

    @property
    def is_averaging(self) -> bool:
        """ """
        return bool(self.handle.query(":sense:average:state?"))

    @is_averaging.setter
    def is_averaging(self, new_is_averaging: bool) -> None:
        """ """
        self.handle.write(f":sense:average:state {int(new_is_averaging)}")

    @property
    def averaging_count(self) -> int:
        """ """
        return int(self.handle.query(":sense:average:sweep?"))

    @property
    def sweep_repetitions(self) -> int:
        """ """
        return int(self.handle.query(":sense:average:count?"))

    @sweep_repetitions.setter
    def sweep_repetitions(self, new_sweep_repetitions: int) -> None:
        """ """
        self.handle.write(":sense:average:clear")  # restart averaging sweep count
        min_, max_ = VNA.MIN_SWEEP_REPETITIONS, VNA.MAX_SWEEP_REPETITIONS
        if not min_ <= new_sweep_repetitions <= max_:
            new_sweep_repetitions = max_
        self.handle.write(f":sense:average:count {new_sweep_repetitions}")

    @property
    def powers(self):
        """ """
        port1_power = float(self.handle.query(":source:power:port1?"))
        port2_power = float(self.handle.query(":source:power:port2?"))
        return (port1_power, port2_power)

    @powers.setter
    def powers(self, new_powers) -> None:
        try:
            port1_power, port2_power = new_powers
        except (TypeError, ValueError):
            raise ValueError("Setter expects (float, float)") from None
        else:
            self.handle.write(f":source:power:port1 {port1_power}")
            self.handle.write(f":source:power:port2 {port2_power}")

    @property
    def traces(self):
        """ """
        return self._traces

    @traces.setter
    def traces(self, new_traces) -> None:
        """ """
        num_traces, min_, max_ = len(new_traces), VNA.MIN_TRACES, VNA.MAX_TRACES
        if not min_ <= num_traces <= max_:
            raise ValueError(f"Number of measured traces must be in [{min_}, {max_}]")
        self.handle.write(f":calculate:parameter:count {num_traces}")
        for count, trace_info in enumerate(new_traces, start=1):
            s_param, trace_format = trace_info
            if s_param.lower() not in VNA.VALID_S_PARAMETERS:
                raise ValueError(f"Invalid S-parameter '{s_param}'")
            if trace_format.lower() not in VNA.VALID_TRACE_FORMATS:
                raise ValueError(f"Invalid format '{trace_format}'")
            self.handle.write(f":calculate:parameter{count}:define {s_param}")
            self.handle.write(f":calculate:parameter{count}:format {trace_format}")

        self._traces = new_traces

        # adjust trace display on shockline app
        layout = VNA.DEFAULT_TRACE_LAYOUT[num_traces]
        self.handle.write(f":display:window:split {layout}")
