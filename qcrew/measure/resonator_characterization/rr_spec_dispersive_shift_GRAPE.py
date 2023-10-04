"""
A python class describing a readout resonator spectroscopy with qubit in ground and 
excited state using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------
class RRSpecDispersiveShiftGRAPE(Experiment):
    name = "rr_spec_dispersive_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, qubit_grape, cav_grape, fit_fn=None, **other_params):
        self.fit_fn = fit_fn
        self.qubit_op = qubit_op
        self.qubit_grape = qubit_grape
        self.cav_grape = cav_grape
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, qubit, cav,) = self.modes  # get the modes
        
        qubit.play(self.qubit_grape, ampx=self.y)
        cav.play(self.cav_grape, ampx=self.y)
        qua.align()
        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q), ampx=1)  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    x_start = 49e6
    x_stop = 51e6
    x_step = 0.05e6

    parameters = {
        "modes": ["RR", "QUBIT", "CAV"],
        "reps": 500,
        "wait_time": 10e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0.0, 1.0],
        "qubit_op": "",
        "qubit_grape": "grape_fock8_pulse",
        "cav_grape": "grape_fock8_pulse",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        # "plot_quad": "I_AVG",
        "fetch_period": 4,
        "fit_fn": None,
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        # "plot_err": None,
    }

    experiment = RRSpecDispersiveShiftGRAPE(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
