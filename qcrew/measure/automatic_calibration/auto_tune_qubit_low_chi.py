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


from qcrew.measure.qubit_experiments_GE.qubit_spec_LK import qubit_spec_LK

# ---------------------------------- Class -------------------------------------


class qubit_spec_LK(Experiment):

    name = "qubit_spec_LK"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        # self.internal_sweep = ["28", "140", "280", "420"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav, flux, qubit_lk = self.modes  # get the modes
        qua.reset_frame(qubit_lk.name)
        qua.update_frequency(qubit_lk.name, self.x)  # update resonator pulse frequency
        qubit_lk.play(self.qubit_op)  # play qubit pulse
        qua.align()

        # flux.play("constcos80ns_2000ns_E2pF2pG2pH2", ampx=-0.258)
        # qua.wait(int(300 // 4), rr.name, "QUBIT_EF")  # ns

        if 1:
            flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.568)  # lk
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.1)  # rr
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0524)  # hk

        # qua.play("digital_pulse", "QUBIT_EF")
        qua.update_frequency(qubit_lk.name, int(-250e6), keep_phase=True)
        qua.play("digital_pulse", qubit_lk.name)
        rr.measure((self.I, self.Q), ampx=0)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, 4Q, x, etc)
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    freq_target = -50.0e6

    slope = 378.4e9 #371.6e9  # 
    current_max = -0.95e-3
    current_min = -0.975e-3
    current_step = 0.0001e-3

    spec_min = -60e6
    spec_max = -40e6
    spec_step = 0.2e6

    parameters_qubit_spec = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
        "reps": 5000,
        "wait_time": 60e3,
        "x_sweep": (int(spec_min), int(spec_max + spec_step / 2), int(spec_step)),
        "qubit_op": "gaussian_pi_400_lk",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fit_fn": "gaussian",
    }

    plot_parameters = {"skip_plot": False, "plot_err": False}

    with Stagehand() as stage:
        qm = stage.QM
        yoko = stage.YOKO

        # Check qubit frequency
        parameters_qubit_spec["modes"] = [
            stage.QUBIT,
            stage.RR,
            stage.CAVITY,
            stage.FLUX,
            stage.QUBIT_LK,
        ]
        experiment_check_qubit_freq = qubit_spec_LK(**parameters_qubit_spec)
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
            params = fit.do_fit("gaussian", freqs, state)
            qubit_freq = float(params["x0"].value)

            ### Calculate current to get target qubit frequency
            current_initial = yoko.level
            current_target = current_initial + (freq_target - qubit_freq) / slope
            if current_max > current_target > current_min:
                yoko.ramp(current_target, yoko.level, np.abs(current_step))

            print("Changed YOKO bias to ", current_target)
