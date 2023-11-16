"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
from qcrew.control import Stagehand
from qcrew.control.pulses.numerical_pulse import NumericalPulse

# ---------------------------------- Class -------------------------------------


class NSplitSpectroscopy(Experiment):

    name = "number_split_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op_measure",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op_measure, cav_op, qubit_op, fit_fn=None, **other_params):

        self.qubit_op_measure = qubit_op_measure
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes

        # Vacuum rabi:
        # with qua.switch_(self.y):
        #     with qua.case_(0):
        #         qubit.play("gaussian_pi", ampx=0)
        #     with qua.case_(1):
        #         # Fock satae preparation
        #         qubit.play("gaussian_pi")
        #         qua.align(qubit.name, flux.name)
        #         flux.play(f"constcos6ns_reset_1to2_28ns_E2pF2pG2pH2", ampx=0.1458)
        #         qua.align()
        #     with qua.case_(2):
        #         # Fock satae preparation
        #         qubit.play("gaussian_pi")
        #         qua.align(qubit.name, flux.name)
        #         flux.play(f"constcos6ns_reset_1to2_28ns_E2pF2pG2pH2", ampx=0.1458)
        #         qua.align()
        #         # Fock satae 2 preparation
        #         qubit.play("gaussian_pi")
        #         qua.align(qubit.name, flux.name)
        #         flux.play(f"constcos2ns_reset_1to2_23ns_E2pF2pG2pH2", ampx=0.25)

        #     # Fock satae 2 preparation
        #     qubit.play("gaussian_pi")
        #     qua.align(qubit.name, flux.name)
        #     flux.play(f"constcos2ns_reset_1to2_23ns_E2pF2pG2pH2", ampx=0.25)

        cav.play(self.cav_op, ampx=1.7)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        # number splitting
        qua.update_frequency(qubit.name, self.x)
        qubit.play(self.qubit_op_measure)  # play qubit pulse
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align modes
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -98e6
    x_stop = -92e6
    x_step = 0.2e6

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 10000,
        "wait_time": 1e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": (0, 1,),
        "qubit_op_measure": "gaussian_pi_320",
        "qubit_op": "gaussian_pi_320",
        "cav_op": "cohstate_1_short",
        # "single_shot": True,
        # "fit_fn": "gaussian",
        "fetch_period": 5,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }
    # flux_len_list = [72]

    # with Stagehand() as stage:
    #     flux = stage.FLUX
    #     for flux_len in flux_len_list:
    #         flux.operations = {
    #             f"castle_IIR_230727_{flux_len}": NumericalPulse(
    #                 path=f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/fast_flux_pulse/castle_max/castle_IIR_230727_{flux_len}ns_0dot06.npz",
    #                 I_quad="I_quad",
    #                 Q_quad="Q_quad",
    #                 ampx=1,
    #             ),
    #         }

    experiment = NSplitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
