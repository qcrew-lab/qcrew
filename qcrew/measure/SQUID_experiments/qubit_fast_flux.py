"""
A python class describing a qubit spectroscopy using QM for different values of
current in a current source.
This class serves as a QUA script generator with user-defined parameters.
"""

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher

from qcrew.helpers.datasaver import DataSaver, initialise_database

from qcrew.analyze.plotter import Plotter
from qcrew.analyze import stats

from qcrew.measure.qubit_experiments_GE.qubit_spec import QubitSpectroscopy
from qcrew.measure.resonator_characterization.rr_spec import RRSpectroscopy

import numpy as np
import h5py
import time


class QubitSpectroscopyCurrent(Experiment):

    name = "qubit_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="lorentzian", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    time_start = 0e-6
    time_stop = 5e-6
    time_step = 0.2e-6
    time_sweep = np.arange(current_start, current_stop, current_step)

    flux_length = 2e-6

    current = 10e-3

    qubit_lo_start = 4.7963e9
    qubit_lo_stop = 4.7962e9
    qubit_lo_step = -200e6
    qubit_lo_sweep = np.arange(qubit_lo_start, qubit_lo_stop, qubit_lo_step)
    # right now only have 1 qubit LO

    # Store information in lists to print later
    filename_list = []
    current_list = []
    lo_list = []
    rr_if_list = []

    # Initialize database for compiling whole experimental data
    with Stagehand() as stage:

        db = initialise_database(
            exp_name="qubit_spec_current_sweep",
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )

        with DataSaver(db) as datasaver:
            experiment_no = 1
            for time in time_sweep:
                """
                # Change value of current source
                yoko = stage.YOKO
                yoko.source = "current"
                yoko.level = current  # set output to nominal value
                yoko.state = True

                """

                # proceed with qubit spectroscopy
                for qubit_lo in qubit_lo_sweep:

                    ## Change qubit LO
                    stage.QUBIT.lo_freq = qubit_lo

                    x_start = -100e6
                    x_stop = 0e6
                    x_step = 0.5e6

                    qubit_spec_parameters = {
                        "modes": [stage.QUBIT, stage.RR],
                        "reps": 2000,
                        "wait_time": 40000,
                        "x_sweep": (
                            int(x_start),
                            int(x_stop + x_step / 2),
                            int(x_step),
                        ),
                        "qubit_op": "constant_pulse",
                        "fit_fn": None,
                        "fetch_period": 2,
                    }

                    qubit_spec_plot_parameters = {
                        "xlabel": "Qubit pulse frequency (Hz) (LO = %.3f GHz)"
                        % (qubit_lo / 1e9),
                    }

                    qubit_spec = QubitSpectroscopy(**qubit_spec_parameters)
                    qubit_spec.setup_plot(**qubit_spec_plot_parameters)
                    plotter = Plotter(qubit_spec.plot_setup)

                    ##### run qubit spectroscopy #####
                    # prof.run_with_stage(qubit_spec, stage)
                    stderr = (None, None, None)
                    qua_program = qubit_spec.QUA_sequence()
                    qm = stage.QM
                    qm_job = qm.execute(qua_program)
                    fetcher = QMResultFetcher(handle=qm_job.result_handles)

                    while fetcher.is_fetching:
                        # Fetch partial results
                        partial_results = fetcher.fetch()
                        num_results = fetcher.count
                        if not partial_results:
                            # empty dict means no new results available
                            continue

                        # Calculate standard error
                        stderr = qubit_spec.estimate_sd(
                            stats, partial_results, num_results, stderr
                        )

                        # post-process and live plot available results
                        qubit_spec_data = qubit_spec.plot_results(
                            plotter, partial_results, num_results, stderr
                        )
                        # prevent over-fetching, over-saving, ultra-fast plotting
                        time.sleep(qubit_spec.fetch_period)

                    ## Correct floor of z_avg
                    z_avg = np.array(qubit_spec_data["Z_AVG"])
                    z_avg -= np.average(z_avg)
                    z_avg = list(z_avg)
                    if current_step < 0:
                        z_avg.reverse()

                    ## Get frequencies
                    freqs = np.array(qubit_spec_data["x"]) + qubit_lo
                    freqs = list(freqs)
                    if current_step < 0:
                        freqs.reverse()

                    # save data
                    exp_tag = "exp_%d" % experiment_no
                    current_sweep_data = {
                        "current": float(current),
                        "qubit_LO": float(qubit_lo),
                        "Z_AVG": np.array(z_avg),
                        "freqs": np.array(freqs),
                    }

                    datasaver.add_multiple_results(
                        current_sweep_data,
                        save=current_sweep_data.keys(),
                        group="data/" + exp_tag,
                    )

                    experiment_no += 1

            yoko = stage.YOKO
            yoko.state = False
