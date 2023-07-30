"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Wigner1D(Experiment):

    name = "wigner_1d_flux"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        cav_op,
        qubit_op,
        qubit_op_wigner,
        cav_op_wigner,
        delay,
        cut,
        fit_fn="gaussian",
        **other_params
    ):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.qubit_op_wigner = qubit_op_wigner
        self.cav_op_wigner = cav_op_wigner
        self.fit_fn = fit_fn
        self.delay = delay
        self.cut = cut

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav, flux = self.modes  # get the modes

        qua.reset_frame(cav.name)

        if 1:  # castle predistorted
            flux.play(
                "castle_IIR_230727_76", ampx=0.574
            )  # to make off resonance
            qua.wait(int((650) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
            qua.wait(int((250) // 4), rr.name, qubit.name)

        qua.align(cav.name, qubit.name)
        # Wigner 1d
        ## single displacement
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.cut, self.x, -self.x, -self.cut),
            phase=0.5,  # 0.25
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align()
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.8
    x_stop = 1.8
    x_step = 0.1


    parameters = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
        "reps": 1000,
        "wait_time": 1.25e6,  # 700e3 #ns
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "cut": 0.0,
        "qubit_op": "qctrl_fock_0p1",
        "cav_op": "qctrl_fock_0p1",
        "qubit_op_wigner": "gaussian_pi2",
        "cav_op_wigner": "const_cohstate_1",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fit_fn": "gaussian",
        "delay": 250,  # pi/chi 208 ns
        "fetch_period": 5,
    }

    plot_parameters = {
        "xlabel": "X",
        # "ylabel": "Y",
        # "plot_type": "2D",
        # "cmap": "bwr",
        # "plot_err": None,
    }

    experiment = Wigner1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
