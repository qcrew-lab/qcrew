"""
A python class describing a cavity T2 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------
class CavityT2(Experiment):
    name = "cavity_T2"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_sel_op",
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_sel_op, detuning, fit_fn="exp_decay_sine", **other_params):
        self.detuning = detuning
        self.cav_op = cav_op
        self.qubit_sel_op = qubit_sel_op
        self.fit_fn = fit_fn
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        # Prepare initial state (|0> + |1>)/sqrt(2)
        
        # factor = qua.declare(qua.fixed)
        # qua.assign(factor, self.detuning * 4 * 1e-9)
        
        qua.update_frequency(cav.name, cav.int_freq + self.detuning)  # detune

        cav.play(self.cav_op, ampx=0.561)  # displace by beta = 0.56
        qua.align(cav.name, qubit.name)  # align pulses
        qubit.play(self.qubit_sel_op, ampx = 2.0)  # SNAP: play pi pulse around X       
        qua.align(cav.name, qubit.name)  # align pulses
        cav.play(self.cav_op, ampx=-0.24)  # displace by beta = -0.26
        
        # Wait relaxation
        qua.wait(self.x, cav.name)

        # Measure cavity state
        cav.play(self.cav_op, phase = 0.5, ampx=0.82)
        qua.align(cav.name, qubit.name)  # align pulses
        qubit.play(self.qubit_sel_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)


        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )


        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 5*250e3
    x_step = 5*1e3

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 1000,
        "wait_time": 10e6,
        "detuning": 1e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_sel_op": "qubit_gaussian_sel_pi_pulse",
        "cav_op": "coherent_1_long",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        "fetch_period": 4,
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
        "plot_err": False,
    }

    experiment = CavityT2(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
