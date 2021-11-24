""" """

import itertools
import pathlib

import numpy as np

from qcrew.control.stage.stagehand import Stagehand
from qcrew.helpers import logger
from vnasavedata import VNADataSaver


class VNASweep:
    """ """

    def __init__(self, vna, repetitions: int, powers: tuple) -> None:
        """ """
        self.repetitions = repetitions
        self.vna = vna

        if self.vna.is_averaging:
            self.vna.sweep_repetitions = repetitions

        is_valid = isinstance(powers, (tuple, list)) and len(powers) == 2
        if not is_valid:
            raise ValueError(f"Expect tuple of length 2, got {powers = }")

        # only frequency sweep, no power sweep specified
        is_fsweep = all(map(lambda x: isinstance(x, (float, int)), powers))
        # power sweep specified
        is_fpsweep = any(map(lambda x: isinstance(x, (tuple, list, set)), powers))
        if is_fsweep:
            self._run = self._run_fsweep
            self.powers = powers
            datashape = (self.repetitions, vna.sweep_points)
        elif is_fpsweep:
            self._run = self._run_fpsweep
            powerlist = []
            for powerspec in powers:
                if isinstance(powerspec, (float, int)):
                    powerlist.append((powerspec,))
                elif isinstance(powerspec, (list, tuple)) and len(powerspec) == 3:
                    start, stop, step = powerspec
                    powerlist.append(np.arange(start, stop + step / 2, step))
                elif isinstance(powerspec, set):
                    powerlist.append(powerspec)
            self.powers = list(itertools.product(*powerlist))
            logger.info(f"Found {len(self.powers)} input power combinations specified")
            datashape = (self.repetitions, len(self.powers), vna.sweep_points)
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
        self._run(saver)  # runs fsweep or fpsweep based on sweep initialization

    def _run_fsweep(self, saver) -> None:
        """ """
        self.vna.powers = self.powers  # set input power on the VNA
        for rep in range(self.repetitions):
            self.vna.sweep()
            saver.save_data(self.vna.data, pos=(rep,))  # save to root group
            logger.info(f"Frequency sweep count = {rep+1} / {self.repetitions}")

    def _run_fpsweep(self, saver) -> None:
        """ """
        # save power data since its already available
        powers = np.array(tuple(self.powers)).T
        saver.save_data({"power1": powers[0], "power2": powers[1]})

        # for each power tuple in self.powers, do fsweep, for n reps
        for power_count, (p1, p2) in enumerate(self.powers):  # p1, p2 = port powers
            self.vna.powers = (p1, p2)  # set input power on the VNA
            logger.info(f"Set power = ({p1}, {p2})")
            for rep in range(self.repetitions):
                self.vna.sweep()
                saver.save_data(self.vna.data, pos=(rep, power_count))
                logger.info(f"Frequency sweep repetition {rep+1} / {self.repetitions}")
            if self.vna.is_averaging:
                self.vna.reset_averaging_count()


if __name__ == "__main__":

    with Stagehand() as stage:
        # connect to VNA
        vna = stage.VNA
        vna.connect()

        # these parameters are set on VNA and do not change during the measurement run
        vna_parameters = {
            # frequency sweep center (Hz)
            "fcenter": 7.346e9,
            # frequency sweep span (Hz)
            "fspan": 20e6,
            # frequency sweep start value (Hz)
            #"fstart": 4e9,
            # frequency sweep stop value (Hz)
            #"fstop": 8e9,
            # IF bandwidth (Hz), [1, 500000]
            "bandwidth": 1e2,
            # number of frequency sweep points, [2, 200001]
            "sweep_points": 2501,
            # delay (s) between successive sweep points, [0.0, 100.0]
            "sweep_delay": 1e-3,
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

        # these parameters are looped over during the measurement
        measurement_parameters = {
            # Number of sweep averages, must be an integer > 0
            "repetitions": 100,
            # Input powers at (<port1>, <port2>) (dBm), range [-30.0, 15.0]
            # <portX> (X=1,2) can be a set {a, b,...}, tuple (st, stop, step), or constant x
            # use set for discrete sweep points a, b, ...
            # use tuple for linear sweep given by np.arange(start, stop + step/2, step)
            # use constant to not sweep power for that port
            # if both <port1> and <port2> are not constant, sweep points will be the cartesian product of <port1> and <port2>
            # eg 1: powers = ((-30, 15, 5), 0) will sweep port 1 power from -30dBm to 15dBm inclusive in steps of 5dBm with port 2 power remaining constant at 0 dBm
            # eg 2: powers = ({-15, 0, 15}, {-5, 0}) will result in sweep points (-15, -5), (-15, 0), (0, -5), (0, 0), (15, -5), (15, 0)
            # eg 3: powers = (0, 0) will set both port powers to 0, no power sweep happens
            "powers": ((-30, 15, 5), 0),
        }

        # create measurement instance with instruments and measurement_parameters
        measurement = VNASweep(vna, **measurement_parameters)
        measurement_parameters["powers"] = measurement.powers

        # hdf5 file saved at:
        # {datapath} / {YYYYMMDD} / {HHMMSS}_{measurementname}_{usersuffix}.hdf5
        save_parameters = {
            "datapath": pathlib.Path(stage.datapath) /"coaxmux",
            "usersuffix": "7.35GHz",
            "measurementname": measurement.__class__.__name__.lower(),
            **measurement.dataspec,
        }

        # run measurement and save data
        #fcenters = [5.3543e9, 5.93454e9, 6.12576e9]
        #vna_parameters["fcenter"] = fcenter
        #vna.fcenter = fcenter
        #save_parameters["usersuffix"] = f"{fcenter:.2}GHz"
        with VNADataSaver(**save_parameters) as vnadatasaver:
            vnadatasaver.save_metadata({**vna_parameters, **measurement_parameters})
            measurement.run(saver=vnadatasaver)
            vna.hold()
        logger.info("Done vnasweep!")
