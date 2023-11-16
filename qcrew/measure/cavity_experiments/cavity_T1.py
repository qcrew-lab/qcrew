"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityT1(Experiment):

    name = "cavity_T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }
    # cohstate_decay
    def __init__(self, cav_op, qubit_op, fit_fn="cohstate_decay", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes

        cav.play(self.cav_op, ampx=2)  # play displacement to cavity
        # cav.play(self.cav_op, ampx=1)  # play displacement to cavity
        qua.wait(self.x, cav.name)  # wait relaxation
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse

        qua.align()  # wait qubit pulse to end
        # flux.play("constcos10ns_1500ns_E2pF2pG2pH2", ampx=-0.2)
        #flux.play("constcos80ns_2000ns_E2pF2pG2pH2", ampx=-0.4)
        # flux.play("constcos10ns_1500ns_E2pF2pG2pH2", ampx=0.18) #constcos80ns_2000ns_E2pF2pG2pH2
        qua.wait(50, rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 1
    x_stop = 60e3
    x_step = 1.5e3
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 5000,
        "wait_time": 1e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "gaussian_pi_560",
        "cav_op": "gaussian_cohstate_1",
        "fetch_period": 20,
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
    }

    experiment = CavityT1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
