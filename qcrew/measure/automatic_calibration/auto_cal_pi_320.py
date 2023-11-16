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


class PowerRabi(Experiment):

    name = "power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, pulse_number, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.pulse_number = pulse_number
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        for i in range(self.pulse_number):
            qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.9
    amp_stop = 1.91
    amp_step = 0.1
    
    pulse_number = 1
    
    parameters = {
        "pulse_number": pulse_number,
        "modes": ["QUBIT", "RR"],
        "reps": 10000,
        "wait_time": 80000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "gaussian_pi_320",
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {"skip_plot": False, "plot_err": False}

    with Stagehand() as stage:
        qm = stage.QM
        yoko = stage.YOKO

        # Check qubit frequency
        parameters["modes"] = [stage.QUBIT, stage.RR]
        experiment_check_qubit_freq = PowerRabi(**parameters)
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
            params = fit.do_fit("sine", freqs, state)
            osc_frequency = float(params["f0"].value)

            ### Calculate current to get target qubit frequency
            ampx_factor = 0.5*pulse_number/osc_frequency
            ampx = stage.QUBIT.gaussian_pi_320.ampx
            stage.QUBIT.gaussian_pi_320.ampx = ampx*ampx_factor

            print("Changed gaussian_pi_320 ampx to ", ampx*ampx_factor)
