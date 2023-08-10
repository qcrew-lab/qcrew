from typing import ClassVar
from unicodedata import ucd_3_2_0

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class UVCompression(Experiment):

    name = "UV_compression"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # operation for displacing the cavity
        "qubit_pi",
        "qubit_pi2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
        "ecd_displacement",
        "u1",
        "v1",
        "u2",
        "v2",
        "u3",
        "v3",
    }

    def __init__(
        self,
        char_func_displacement,
        qubit_pi,
        qubit_pi2,
        ecd_displacement,
        u1,
        v1,
        u2,
        v2,
        u3,
        v3,
        fit_fn=None,
        delay=4,
  
        measure_real=True,
        **other_params
    ):
        self.char_func_displacement = char_func_displacement
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.ecd_displacement = ecd_displacement
        self.u1 = u1
        self.v1 = v1
        self.u2 = u2
        self.v2 = v2
        self.u3= u3
        self.v3 = v3
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.reset_phase(qubit.name)

        # state creation
        
        if 1:

            U(
                cav,
                qubit,
                self.ecd_displacement,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u1,
                delay=self.delay,
            )

        if 1:
            V(
                cav,
                qubit,
                self.ecd_displacement,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v1,
                delay=self.delay,
            )
            
        if 0:

          U(
              cav,
              qubit,
              self.ecd_displacement,
              self.qubit_pi,
              self.qubit_pi2,
              ampx=self.u2,
              delay=self.delay,
          )

        if 0:
            V(
                cav,
                qubit,
                self.ecd_displacement,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v2,
                delay=self.delay,
            )
        if 0:

          U(
              cav,
              qubit,
              self.ecd_displacement,
              self.qubit_pi,
              self.qubit_pi2,
              ampx=self.u3,
              delay=self.delay,
          )

        if 0:
            V(
                cav,
                qubit,
                self.ecd_displacement,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v3,
                delay=self.delay,
            )

        ######################  Measure the created state with charactristic function  #####################
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=0,
        )

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
  
    x_start = -1.02
    x_stop = 1.02
    x_step = 0.05

    y_start = -1.02
    y_stop = 1.02
    y_step = 0.05
    
    ecd_factor = 2
    compression_3db_1step = np.array([1,
                             -0.6,
                             -0.48,
                             1.04,
                             -1.11,
                             -0.32])/ecd_factor

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 1000000,
        "wait_time": 200e3,
        "fetch_period": 3,  # time between data fetching rounds in sec
        "delay": 100,  # wait time between opposite sign displacements
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi": "pi",
        "qubit_pi2": "pi2",
        "char_func_displacement": "bob_ecd_3",
        "ecd_displacement" : "bob_ecd_1",
        "u1" : compression_3db_1step[0], 
        "v1" : compression_3db_1step[1],
        "u2" : compression_3db_1step[2], 
        "v2" : compression_3db_1step[3],
        "u3" : compression_3db_1step[4], 
        "v3" : compression_3db_1step[5], 
        "measure_real": True,
        "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = UVCompression(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
