"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

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

        flux.play("constcos80ns_2000ns_E2pF2pG2pH2", ampx=-0.258)  ## lower chi
        qua.wait(int(300 // 4), rr.name, qubit_lk.name)  # ns

        qua.update_frequency(qubit_lk.name, int(-250e6), keep_phase=True)
        qua.play("digital_pulse", qubit_lk.name)
        rr.measure((self.I, self.Q), ampx=0)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait syst em reset

        if self.single_shot:  # assign state to G or
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, 4Q, x, etc)
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    ## char
    # x_start =-180e6
    # x_stop = -170e6
    # x_step = 0.1e6

    ## rr
    # x_start =-140e6
    # x_stop = -120e6
    # x_step = 0.2e6
    # ## high kerr
    # x_start = -95e6
    # x_stop = -90e6
    # x_step = 0.2e6
    ## low kerr
    x_start = -60e6
    x_stop = -45e6
    x_step = 0.2e6

    parameters = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX", "QUBIT_LK"],
        "reps": 500000,
        "wait_time": 60e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "gaussian_pi_400_lk",  # gaussian_pi_400_lk
        "plot_quad": "I_AVG",
        # "single_shot": True,
        "fit_fn": "gaussian",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = qubit_spec_LK(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
