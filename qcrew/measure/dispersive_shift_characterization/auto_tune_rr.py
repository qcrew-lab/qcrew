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


class RRSpectroscopy(Experiment):

    name = "rr_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, fit_fn=None, **other_params):

        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr,) = self.modes  # get the modesz
        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequenc
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -54e6
    x_stop = -42e6
    x_step = 0.05e6

    parameters = {
        "modes": [
            "RR",
        ],
        "reps": 1000,
        "wait_time": 20000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "fit_fn": "gaussian",
    }

    plot_parameters = {"skip_plot": False, "plot_err": False}

    with Stagehand() as stage:
        qm = stage.QM
        yoko = stage.YOKO

        # Check qubit frequency
        parameters["modes"] = [stage.RR]
        experiment_check_qubit_freq = RRSpectroscopy(**parameters)
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

            state = np.array(qubit_spec_data["Z_AVG"])
            freqs = np.array(qubit_spec_data["x"])
            params = fit.do_fit("gaussian", freqs, state)
            rr_freq = float(params["x0"].value)//10e3*10e3
            stage.RR.int_freq = rr_freq

            print("Changed RR IF to ", rr_freq)
