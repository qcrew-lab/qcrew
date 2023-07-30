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
        # qua.reset_frame(cav.name)
        qua.update_frequency(qubit.name, qubit.int_freq)  # update qubit pulse frequency
        # cav.play(self.cav_op, ampx=self.cav_amp)  # prepare cavity state
        # prepare fock state in cav

        # fock state
        with qua.if_(self.y):
            if 0: #normal pulse
                qubit.play("gaussian_pi")  # play pi qubit pulse
                qua.align(qubit.name, flux.name)
                flux.play(f"predist_constcos_10ns_64ns", ampx=-0.16)
                qua.wait(int((470 + 20000) // 4))
            if 1: #pre       
                qua.wait(115, qubit.name)
                qubit.play(self.qubit_op)  # play pi qubit pulse
                flux.play(f"castle_IIR_230727_72", ampx=0.51)  # ns
                qua.wait(int((1100 + 24) // 4), rr.name, qubit.name)  # cc
                rr.measure((self.I, self.Q))  # measure qubit state


        # number splitting
        qua.update_frequency(qubit.name, self.x)
        qubit.play(self.qubit_op_measure)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -90e6
    x_stop = -75e6
    x_step = 0.05e6

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 500,
        "wait_time": 1.25e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (False, True),
        "qubit_op_measure": "gaussian_pi_280",
        # "cav_op": "const_cohstate_1",
        "qubit_op": "qctrl_fock_1",
        "cav_op": "qctrl_fock_1",
        "single_shot": True,
        "fit_fn": "gaussian",
        "fetch_period": 8,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }
    flux_len_list = [72]
    
    with Stagehand() as stage:
        flux = stage.FLUX
        for flux_len in flux_len_list:
            flux.operations = {
                f"castle_IIR_230727_{flux_len}": NumericalPulse(
                    path=f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/fast_flux_pulse/castle_max/castle_IIR_230727_{flux_len}ns_0dot06.npz",
                    I_quad="I_quad",
                    Q_quad="Q_quad",
                    ampx=1,
                ),
            }

    experiment = NSplitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
