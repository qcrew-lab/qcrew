""" """


import pathlib
import time

import numpy as np
from qcrew.control.stage.stagehand import Stagehand
from qcrew.helpers import logger

from vnasavedata import VNADataSaver

class PumpPowerSweep:
    """ """

    def __init__(self, vna, pump, repetitions: int, powers: tuple) -> None:
        """ """
        self.repetitions = repetitions
        self.vna = vna
        self.pump = pump
        self.vna.is_averaging = (
            False  # if you set to True, VNA will give you averaged data, not raw data
        )

        self._run = self._run_fpsweep  # by default, run freq & pow sweep
        if isinstance(powers, tuple) and len(powers) == 3:
            start, stop, step = powers
            self.powers = np.arange(start, stop + step / 2, step).round(7)
            datashape = (self.repetitions, len(self.powers), vna.sweep_points)
        elif isinstance(powers, set):
            self.powers = sorted(powers)
            datashape = (self.repetitions, len(self.powers), vna.sweep_points)
        elif isinstance(powers, (int, float)):
            self.powers = powers
            self._run = self._run_fsweep
            datashape = (self.repetitions, vna.sweep_points)
        else:
            raise ValueError(f"Invalid specification of {powers = }")

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
        self.pump.power = -20  # nominal value
        self.pump.rf = True

        self._run(saver)  # runs fsweep or fpsweep based on sweep initialization

        self.pump.rf = False

    def _run_fsweep(self, saver) -> None:
        self.pump.power = self.powers
        for rep in range(self.repetitions):
            self.vna.sweep()
            saver.save_data(self.vna.data, pos=(rep,))  # save to root group
            logger.info(f"Frequency sweep count = {rep+1} / {self.repetitions}")

    def _run_fpsweep(self, saver) -> None:
        # save power data since its already available
        saver.save_data({"power": self.powers})

        num_powers = len(self.powers)
        # for n reps, for each pump power in self.powers, do fsweep
        for rep in range(self.repetitions):
            logger.info(f"Repetition: {rep+1}/{self.repetitions}")
            for count, power in enumerate(self.powers):
                self.pump.power = power
                logger.info(f"Set {power = }, sweep count: {count+1}/{num_powers}")
                time.sleep(0.1)  # for signalcore output level to stabilize
                self.vna.sweep()
                saver.save_data(self.vna.data, pos=(rep, count))

if __name__ == "__main__":

    with Stagehand() as stage:
        # connect to VNA
        vna = stage.VNA
        vna.connect()  # this is needed to switch back to remote mode
        pump = stage.CORE_B

        # these parameters are set on VNA and do not change during the measurement run
        vna_parameters = {
            # frequency sweep center (Hz)
            #"fcenter": 6.12725e9,
            # frequency sweep span (Hz)
            #"fspan": 20e6,
            # frequency sweep start value (Hz)
            "fstart": 4e9,
            # frequency sweep stop value (Hz)
            "fstop": 9e9,
            # IF bandwidth (Hz), [1, 500000]
            "bandwidth": 1e3,
            # number of frequency sweep points, [2, 200001]
            "sweep_points": 501,
            # delay (s) between successive sweep points, [0.0, 100.0]
            "sweep_delay": 1e-3,
            # input powers (port1, port2)
            "powers": (-30, -30),
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
            "is_averaging": False,
        }
        vna.configure(**vna_parameters)
        
        # set pump frequency
        pump.frequency = 5e9

        # these parameters are looped over during the measurement
        measurement_parameters = {
            # Number of sweep averages, must be an integer > 0
            "repetitions": 5,
            # Input powers from pump
            # "powers" can be a set {a, b,...}, tuple (st, stop, step), or constant x
            # use set for discrete sweep points a, b, ...
            # use tuple for linear sweep given by np.arange(start, stop + step/2, step) (inclusive of start and stop)
            # use constant to get a frequency sweep at constant powers
            # eg 1: powers = (-10, 0, 1) will sweep powers from -10dBm to 0dBm inclusive in steps of 1dBm
            # eg 2: powers = {-15, 0, 15} will sweep power at -15dBm, 0dBm, and 15dBm
            # eg 3: powers = 0 will do a frequency sweep at constant power of 0 dBm i.e. no power sweep
            "powers": (-20, -10, 3),
        }

        # create measurement instance with instruments and measurement_parameters
        measurement = PumpPowerSweep(vna, pump, **measurement_parameters)

        # hdf5 file saved at:
        # {datapath} / {YYYYMMDD} / {HHMMSS}_{measurementname}_{usersuffix}.hdf5
        save_parameters = {
            "datapath": pathlib.Path(stage.datapath) / "djint",
            "usersuffix": "test",
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
            logger.info("Done pump power sweep!")

        # use this code to plot after msmt is done
        import h5py
        import matplotlib.pyplot as plt
        file = h5py.File(filepath, "r")
        data = file["data"]
        s21_mlog = data["s21_mlog"]
        pows = data["power"]
        freqs = data["frequency"]
        s21_mlog_avg = np.mean(s21_mlog, axis=0)
        plt.figure(figsize=(12, 8))
        plt.pcolormesh(pows, freqs, s21_mlog_avg.T, cmap="twilight_shifted", shading="auto")
        plt.colorbar()
        plt.show()
