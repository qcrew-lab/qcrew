"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import Stagehand
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qcrew.analyze import fit
from qm import qua
import matplotlib.pyplot as plt
import numpy as np
import h5py


import time
import numpy as np

from qcrew.analyze import stats
from qcrew.analyze.plotter import Plotter
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.helpers import logger
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.measure.experiment import Experiment

import matplotlib.pyplot as plt
from IPython import display


from qcrew.measure.qubit_experiments_GE.qubit_spec import QubitSpectroscopy

# ---------------------------------- Class -------------------------------------


class CavityDisplacementCal(Experiment):

    name = "cavity_displacement_cal"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="displacement_cal", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes

        cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        # qua.align()

        qua.align(qubit.name, flux.name, rr.name)  # align measurement
        flux.play("square_2200ns_ApBpC", ampx=-0.5)
        qua.wait(50, rr.name)

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 0.0
    x_stop = 1.91
    x_step = 0.15
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 5000,
        "wait_time": 0.6e6,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_op": "gaussian_pi_320",
        "cav_op": "cohstate_1",
        # "fetch_period": 2,
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {"skip_plot": False, "plot_err": False}

    with Stagehand() as stage:
        qm = stage.QM
        yoko = stage.YOKO

        # Check qubit frequency
        parameters["modes"] = [stage.QUBIT, stage.CAVITY, stage.RR, stage.FLUX]
        experiment_check_qubit_freq = CavityDisplacementCal(**parameters)
        experiment_check_qubit_freq.setup_plot(**plot_parameters)
        qua_program = experiment_check_qubit_freq.QUA_sequence()
        qm_job = qm.execute(qua_program)

        fetcher = QMResultFetcher(handle=qm_job.result_handles)
        stderr = (
            None,
            None,
            None,
        )  # to hold running (stderr, mean, variance * (n-1))

        db = initialise_database(
            exp_name=experiment_check_qubit_freq.name,
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )

        experiment_check_qubit_freq.filename = db.filename
        plotter = Plotter(experiment_check_qubit_freq.plot_setup)
        with DataSaver(db) as datasaver:
            datasaver.add_metadata(experiment_check_qubit_freq.parameters)
            for mode in stage.modes:
                datasaver.add_metadata(mode.parameters)
            while fetcher.is_fetching:
                partial_results = fetcher.fetch()
                num_results = fetcher.count
                if not partial_results:  # empty dict means no new results available
                    continue
                datasaver.update_multiple_results(
                    partial_results,
                    save=experiment_check_qubit_freq.live_saving_tags,
                    group="data",
                )
                stderr = ([],)
                qubit_spec_data = experiment_check_qubit_freq.plot_results(
                    plotter, partial_results, num_results, stderr
                )
                time.sleep(experiment_check_qubit_freq.fetch_period)

            ##################         SAVE REMAINING DATA         #####################

            datasaver.add_multiple_results(
                qubit_spec_data, save=qubit_spec_data.keys(), group="data"
            )
            state = np.array(qubit_spec_data["I_AVG"])
            freqs = np.array(qubit_spec_data["x"])
            params = fit.do_fit("displacement_cal", freqs, state)
            dispscale = float(params["dispscale"].value)

            ### Calculate current to get target qubit frequency
            ampx = stage.CAVITY.cohstate_1.ampx
            stage.CAVITY.cohstate_1.ampx = ampx / dispscale

            print("Changed gaussian_pi ampx to ", ampx / dispscale)
