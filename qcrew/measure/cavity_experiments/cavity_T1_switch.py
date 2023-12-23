"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class cavity_T1_switch(Experiment):

    name = "cavity_T1_switch"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }
    # cohstate_decay
    def __init__(self, cav_op, qubit_op, fit_fn="exp_decay", **other_params):
        #cohstate_decay
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes
        # qua.reset_frame(cav.name)
        # qua.reset_frame(qubit.name)
        # qua.reset_frame(qubit_lk.name)

        # Coherent state preparation and evolution
     
        cav.play("gaussian_cohstate_1_hk", ampx=1)

        # cav.play(self.cav_op, ampx=0.7)  # play displacement to cavity
        # cav.play(self.cav_op, ampx=1)  # play displacement to cavity
        qua.wait(self.x, cav.name)  # wait relaxation
        qua.align(cav.name, qubit.name)  # align all modes
        with qua.switch_(self.y):
            with qua.case_(0):
                qubit.play("gaussian_pi_t1_160")  # play qubit pulse
            with qua.case_(1):
                qubit.play("gaussian_pi_t1_320")  # play qubit pulse
            with qua.case_(2):
                qubit.play("gaussian_pi_t1_480")  # play qubit pulse
        qua.align()  # wait qubit pulse to end
        # flux.play("constcos10ns_1500ns_E2pF2pG2pH2", ampx=-0.2)
        # flux.play("constcos80ns_2000ns_E2pF2pG2pH2", ampx=-0.4)
     
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
 
    x_start = 1
    x_stop = 120e3  # 60e3
    x_step = 2.5e3
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 2e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "gaussian_pi_hk_320",
        "cav_op": "gaussian_cohstate_1_hk",
        "fetch_period": 60, #10,
        "y_sweep": (0,), #(0, 1, 2,),
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
    }

    experiment = cavity_T1_switch(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
