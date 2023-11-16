import numpy as np
import time
from typing import ClassVar
import pyvisa

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class Apuasyn(Instrument):
    """ """

    _parameters: ClassVar[set[str]] = {
        "channel",
        "frequency",
        "phase",
        "status",
        "power",
        "output",
    }

    def __init__(self, id: str, name="") -> None:
        """ """
        super().__init__(id=id, name=name)
        self.handle: pyvisa.resource.Resource = None
        self.connect()

    def connect(self) -> None:
        """ """
        resource_name = f"USB0::0x03EB::0xAFFF::{self.id}::INSTR"
        try:
            self.handle = pyvisa.ResourceManager().open_resource(resource_name)
            logger.info(self.handle.query("*IDN?"))
        except pyvisa.errors.VisaIOError as err:
            details = f"{err.abbreviation} : {err.description}"
            raise ConnectionError(f"Failed to connect {self}, {details = }") from None

    def _initialize(self) -> None:
        """ """
        # do a self-test to see if instrument is ok
        status = self.handle.query("*TST?")
        if not int(status) == 0:  # if status == 0, all is good
            raise RuntimeError(f"{self} self-test failed, please check the instrument")

    def disconnect(self) -> None:
        """ """
        self.handle.close()

    @property
    def status(self) -> bool:
        """ """
        try:
            self.handle.query("*IDN?")
        except (pyvisa.errors.VisaIOError, pyvisa.errors.InvalidSession):
            return False
        else:
            return True

    @property
    def channel(self) -> int:
        """Returns the current active channel"""
        return int(self.handle.query(f":SEL?"))

    @channel.setter
    def channel(self, value: int) -> None:
        """Sets active channel"""
        self.handle.write(f":SEL {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    @property
    def frequency(self) -> float:
        """Returns freq in Hz"""
        return float(self.handle.query(f":FREQ:CW?"))

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Writes frequency in Hz"""
        self.handle.write(f":FREQ:CW {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    @property
    def phase(self) -> float:
        """Returns phase in rad"""
        return float(self.handle.query(f":PHAS:ADJ?"))

    @phase.setter
    def phase(self, value: float):
        """Writes phase in rad"""
        self.handle.write(f":PHAS:ADJ {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    @property
    def power(self) -> float:
        """Returns power in dBm"""
        return float(self.handle.query(f":POW?"))

    @power.setter
    def power(self, value: float):
        """Sets power in dBm"""
        self.handle.write(f":POW {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    @property
    def output(self) -> bool:
        """ """
        return bool(self.handle.query(f"OUTP?"))

    @output.setter
    def output(self, value: bool):
        """ """
        if value:
            self.handle.write(f"OUTP ON")
        else:
            self.handle.write(f"OUTP OFF")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    def get_channel_freq(self, channel: int) -> float:
        """Returns freq of channel in Hz"""
        return float(self.handle.query(f":SOUR{channel}:FREQ:CW?"))

    def set_channel_freq(self, channel: int, value: float) -> float:
        """Sets freq of channel in Hz"""
        self.handle.write(f":SOUR{channel}:FREQ:CW {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    def get_channel_pow(self, channel: int) -> float:
        """Returns power of channel in dBm"""
        return float(self.handle.query(f":SOUR{channel}:POW?"))

    def set_channel_pow(self, channel: int, value: float) -> float:
        """Sets power of channel in dBm"""
        self.handle.write(f":SOUR{channel}:POW {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    def get_channel_phase(self, channel: int) -> float:
        """Returns phase of channel in rad"""
        return float(self.handle.query(f":SOUR{channel}:PHAS?"))

    def set_channel_phase(self, channel: int, value: float) -> float:
        """Sets phase of channel in rad"""
        self.handle.write(f":SOUR{channel}:PHAS:ADJ? {value}")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")

    def on_channel_output(self, channel: int):
        self.handle.write(f"OUTP{channel}:STAT ON")
        self.handle.query("*OPC?")

    def off_channel_output(self, channel: int):
        self.handle.write(f"OUTP{channel}:STAT OFF")
        self.handle.query("*OPC?")

    def off_all_modulation(self, channel: int):
        """ """
        # Turn off other modulation methods
        # self.handle.write(f":SOUR{channel}:AM:STAT OFF")
        # self.handle.write(f":SOUR{channel}:FM:STAT OFF")
        # self.handle.write(f":SOUR{channel}:PM:STAT OFF")
        self.handle.write(f":SOUR{channel}:PULM:STAT OFF")

    def setup_pulse_mod(self, channel: int) -> bool:
        """ """

        # Sets reference osc to an external source (Rubidium clock)
        self.handle.write(f":SOUR{channel}:ROSC:SOUR EXT")
        # Make sure that freq change happens immediately and not on trigger
        self.handle.write(f":SOUR{channel}:FREQ:TRIG OFF")
        # Set all subsystems to fixed
        self.handle.write(f":SOUR{channel}:FREQ:MODE CW")
        self.handle.write(f":SOUR{channel}:POW:MODE CW")
        self.handle.write(f":SOUR{channel}:PHASE:MODE CW")

        # Turn off other modulation methods
        self.handle.write(f":SOUR{channel}:AM:STAT OFF")
        self.handle.write(f":SOUR{channel}:FM:STAT OFF")
        self.handle.write(f":SOUR{channel}:PM:STAT OFF")

        # Turn on pulse modulation and enable output
        self.handle.write(f":SOUR{channel}:PULM:SOUR EXT")
        self.handle.write(f":SOUR{channel}:PULM:STAT ON")
        self.handle.write(f":OUTP {channel} ON")
        self.handle.write(f":OUTP:BLAN {channel} OFF")
        # Synchronize (wait until all previous commands have been executed completely)
        self.handle.query("*OPC?")
        pulse_mode_src = str(self.handle.query(f":SOUR{channel}:PULM:SOUR?"))
        pulse_mode_on = bool(self.handle.query(f":SOUR{channel}:PULM:STAT?"))

        return (pulse_mode_src == "EXT") and pulse_mode_on

    def setup_freq_sweep(self, channel: int, start: float, stop: float, step: float):
        """ """
        self.handle.write(f"SOUR{channel}:FREQ:MODE SWE")
        self.handle.write(f"SOUR{channel}:FREQ:STAR {start}")
        self.handle.write(f"SOUR{channel}:FREQ:STOP {stop}")
        self.handle.write(f"SOUR{channel}:FREQ:STEP {step}")
        self.handle.write(f":TRIG:TYPE POINT")
