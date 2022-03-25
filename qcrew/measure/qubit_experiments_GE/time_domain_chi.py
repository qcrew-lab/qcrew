from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class time_domain_chi(Experiment):

    name = "time_domain_chi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        # "detuning",  # qubit pulse detuning
    }

    def __init__(self, cav_op, qubit_op, fit_fn="exp_decay_sine", **other_params):

        self.cav_op = cav_op  # operation for displacing the cavity
        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn
        # self.detuning = detuning  # frequency detuning of qubit operation

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)

        cav.play(self.cav_op, ampx=0.5)  # displacement
        qua.align(cav.name, qubit.name)  # align modes

        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay

        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end

        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

 
# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 10
    x_stop = 4000
    x_step = 20

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 2000000,
        "wait_time": 75000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),  # wait time
        "qubit_op": "pi2",
        "cav_op": "pi",
        #"y_sweep":   # displacement
        # "detuning": int(detuning),
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Delay (clock cycles)",
    }

    experiment = time_domain_chi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
