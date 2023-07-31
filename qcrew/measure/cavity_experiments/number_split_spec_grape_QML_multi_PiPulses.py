"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class NSplitSpectroscopy(Experiment):

    name = "number_split_spec_multi_pi_pulse"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, cav_op, cav_amp, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_amp = cav_amp
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_op, ampx=self.cav_amp)  # prepare cavity state
        qua.align()

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -73e6  # -51e6
    x_stop = -62e6  # -49.76e6
    x_step = 0.05e6

    pulselist = [
        "cc_800",        
        "cc_400",        
        "cc_200",        
        "cc_100",        

    ]

    for pulse in pulselist:
        parameters = {
            "modes": ["QUBIT", "CAVA", "RR"],
            "reps": 5000,
            "wait_time": 500e3,
            "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
            # "x_sweep": frearray,
            "qubit_op": pulse,
            "cav_op": "coherent1_gaussian",
            "cav_amp": 1,
            "plot_quad": "I_AVG",
            "fetch_period": 5,
        }

        plot_parameters = {"xlabel": "Qubit pulse frequency (Hz)", "plot_err": None}

        experiment = NSplitSpectroscopy(**parameters)

        experiment.name = "QML_number_split_spec_" + pulse
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
