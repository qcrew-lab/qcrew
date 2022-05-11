""" Play an ecd numerical pulse and measure qfunc """

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ECDNumerical(Experiment):

    name = "ECDNumerical"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, oct_op, fit_fn=None, **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.oct_op = oct_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        # qua.update_frequency(
        #     qubit.name, qubit.int_freq
        # )  # update resonator pulse frequency

        # generate state
        qubit.play(self.oct_op)
        cav.play(self.oct_op)
        qua.align(qubit.name, cav.name)

        # measurement
        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        
        # qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        # qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        # rr.measure((self.I, self.Q))  # measure transmitted signal
        # qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        # measurement of q function
        # cav.play(self.cav_op, ampx=-self.x, phase=0)  # displacement in I direction
        # cav.play(self.cav_op, ampx=-self.y, phase=0.25)  # displacement in Q direction
        # qua.align(cav.name, qubit.name)
        # qubit.play(self.qubit_op)  # play qubit selective pi-pulse
        # # Measure cavity state
        # qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    # x_start = -1.3
    # x_stop = 1.3
    # x_step = 0.05
    
    x_start = 50e6
    x_stop = 50.5e6
    x_step = 0.002e6
    

    # y_start = -1.5
    # y_stop = 1.5
    # y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 100000,
        "wait_time": 100000,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "x_sweep": (
            # x_start,
            # x_stop + x_step / 2,
            # x_step,
            int(x_start),
            int(x_stop + x_step / 2),
            int(x_step),
              
        ),  # ampitude sweep of the displacement pulses in the ECD
        # "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "pi_selective",#"pi_test",
        "cav_op": "cohstate_1_test",
        "oct_op": "oct_pulse",
    }

    plot_parameters = {
        "xlabel": "X",
        # "ylabel": "Y",
        # "plot_type": "2D",
        # "err": False,
        # "cmap": "bwr",
    }

    experiment = ECDNumerical(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
