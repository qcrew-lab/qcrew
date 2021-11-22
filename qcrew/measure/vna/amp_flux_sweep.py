""" """

import pathlib
import time

import numpy as np
from qcrew.control.stage.stagehand import Stagehand
from qcrew.helpers import logger

from vnasavedata import VNADataSaver


class AmpFluxSweep:
    """ """

    def __init__(self, vna, yoko, repetitions: int, currents: tuple) -> None:
        """ """
        self.repetitions = repetitions
        self.vna = vna
        self.yoko = yoko
        self.vna.is_averaging = (
            False  # if you set to True, VNA will give you averaged data, not raw data
        )

        self._run = self._run_fasweep  # by default, run freq & amp sweep
        if isinstance(currents, tuple) and len(currents) == 3:
            start, stop, step = currents
            self.currents = np.arange(start, stop + step / 2, step).round(7)
            datashape = (self.repetitions, len(self.currents), vna.sweep_points)
        elif isinstance(currents, set):
            self.currents = sorted(currents)
            datashape = (self.repetitions, len(self.currents), vna.sweep_points)
        elif isinstance(currents, (int, float)):
            self.currents = currents
            self._run = self._run_fsweep
            datashape = (self.repetitions, vna.sweep_points)
        else:
            raise ValueError(f"Invalid specification of {currents = }")

        # set dataspec
        self.dataspec = {
            "datagroup": "data",
            "datasets": vna.datakeys,  # each group will have datasets of these names
            "datashape": datashape,
            "datatype": "f4",
        }

    def run(self, saver) -> None:
        # save frequency data since its already available and is the same for all sweeps
        saver.save_data({"frequency": self.vna.frequencies})  # arg must be a dict
        self.yoko.source = "current"
        self.yoko.level = 0  # set output to nominal value
        self.yoko.state = "on"

        self._run(saver)  # runs fsweep or fpsweep based on sweep initialization
    
        self.yoko.level = 0
        self.yoko.state = "off"

    def _run_fsweep(self, saver) -> None:
        self.yoko.level = self.currents
        for rep in range(self.repetitions):
            self.vna.sweep()
            saver.save_data(self.vna.data, pos=(rep,))  # save to root group
            logger.info(f"Frequency sweep count = {rep+1} / {self.repetitions}")


    def _run_fasweep(self, saver) -> None:
        # save current data since its already available
        saver.save_data({"current": self.currents})

        num_currents = len(self.currents)
        # for n reps, for each current in self.currents, do fsweep
        for rep in range(self.repetitions):
            logger.info(f"Repetition: {rep+1}/{self.repetitions}")
            for count, current in enumerate(self.currents):
                self.yoko.level = current
                logger.info(f"Set {current = }, sweep count: {count+1}/{num_currents}")
                time.sleep(0.1)  # for yoko output level to stabilize
                self.vna.sweep()
                saver.save_data(self.vna.data, pos=(rep, count))


if __name__ == "__main__":

    with Stagehand() as stage:
        # connect to VNA
        vna = stage.VNA
        yoko = stage.YOKO

        # these parameters are set on VNA and do not change during the measurement run
        vna_parameters = {
            # frequency sweep center (Hz)
            #"fcenter": 6.12725e9,
            # frequency sweep span (Hz)
            #"fspan": 20e6,
            # frequency sweep start value (Hz)
            "fstart": 3e9,
            # frequency sweep stop value (Hz)
            "fstop": 9e9,
            # IF bandwidth (Hz), [1, 500000]
            "bandwidth": 1e3,
            # number of frequency sweep points, [2, 200001]
            "sweep_points": 2501,
            # delay (s) between successive sweep points, [0.0, 100.0]
            "sweep_delay": 1e-3,
            # input powers (port1, port2)
            "powers": (-20, -20),
            # trace data to be displayed and acquired, max traces = 16
            # each tuple in the list is (<S parameter>, <trace format>)
            # valid S parameter keys = ("s11", "s12", "s21", "s22")
            # see VNA.VALID_TRACE_FORMATS for full list of available trace format keys
            "traces": [
                ("s21", "real"),
                ("s21", "imag"),
                ("s21", "mlog"),
                ("s21", "phase"),
            ],
            # if true, VNA will display averaged traces on the Shockline app
            # if false, VNA will display the trace of the current run
            "is_averaging": True,
        }
        vna.configure(**vna_parameters)

        # these parameters are looped over during the measurement
        measurement_parameters = {
            # Number of sweep averages, must be an integer > 0
            "repetitions": 25,
            # Input currents from yoko
            # "currents" can be a set {a, b,...}, tuple (st, stop, step), or constant x
            # use set for discrete sweep points a, b, ...
            # use tuple for linear sweep given by np.arange(start, stop + step/2, step) (inclusive of start and stop)
            # use constant to get a frequency sweep at constant current
            # eg 1: currents = (-10e-6, 0e-6, 1e-6) will sweep current from -10uA to 0uA inclusive in steps of 1uA
            # eg 2: currents = {-15e-6, 0e-6, 15e-6} will sweep curent at -15uA, 0uA, and 15uA
            # eg 3: currents = 0 will do a frequency sweep at constant current of 0uA i.e. no current sweep
            "currents": (0, 6e-3, 0.02e-3),
        }

        # create measurement instance with instruments and measurement_parameters
        measurement = AmpFluxSweep(vna, yoko, **measurement_parameters)

        # hdf5 file saved at:
        # {datapath} / {YYYYMMDD} / {HHMMSS}_{measurementname}_{usersuffix}.hdf5
        save_parameters = {
            "datapath": pathlib.Path(stage.datapath) / "djext",
            "usersuffix": "",
            "measurementname": measurement.__class__.__name__.lower(),
            **measurement.dataspec,
        }

        filepath = None  # will be set by vnadatasaver
        # run measurement and save data
        with VNADataSaver(**save_parameters) as vnadatasaver:
            vnadatasaver.save_metadata({**vna_parameters, **measurement_parameters})
            measurement.run(saver=vnadatasaver)
            vna.hold()
            filepath = vnadatasaver.filepath
            logger.info("Done ampfluxsweep!")

""" 
use this code to plot after msmt is done # TEMPORARY
import h5py
import numpy as np
import matplotlib.pyplot as plt
file = h5py.File(filepath, "r")
s21_phase = file["data"]["s21_phase"]
currs = file["data"]["current"]
freqs = file["data"]["frequency"]
s21_phase_avg = np.mean(s21_phase, axis=0)
plt.figure(figsize=(12, 8))
plt.pcolormesh(currs, freqs, s21_phase_avg.T, cmap="twilight_shifted", shading="auto")
plt.colorbar()
"""