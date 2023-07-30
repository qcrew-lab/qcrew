"""
A python class describing a qubit spectroscopy using QM for different values of
current in a current source.
This class serves as a QUA script generator with user-defined parameters.
"""

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.measure.qubit_experiments_GE.qubit_spec import QubitSpectroscopy

import numpy as np

# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    qubit_lo_start = 6e9
    qubit_lo_stop = 5e9
    qubit_lo_step = -400e6
    qubit_lo_sweep = np.arange(qubit_lo_start, qubit_lo_stop, qubit_lo_step)

    # Store information in lists to print later
    filename_list = []
    lo_list = []
    rr_if_list = []

    # Initialize database for compiling whole experimental data
    with Stagehand() as stage:

        db = initialise_database(
            exp_name="long_qubit_spec",
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )

        with DataSaver(db) as datasaver:
            # proceed with qubit spectroscopy
            for qubit_lo in qubit_lo_sweep:

                ## Change qubit LO
                stage.QUBIT.lo_freq = qubit_lo

                x_start = -200e6
                x_stop = 200e6
                x_step = 0.25e6

                qubit_spec_parameters = {
                    "modes": ["QUBIT", "RR"],
                    "reps": 1000,
                    "wait_time": 15000,
                    "x_sweep": (
                        int(x_start),
                        int(x_stop + x_step / 2),
                        int(x_step),
                    ),
                    "qubit_op": "gaussian_pi",
                    "fetch_period": 2,
                    # "plot_quad": "PHASE",
                }

                qubit_spec_plot_parameters = {
                    "xlabel": "Qubit pulse frequency (Hz) (LO = %.3f GHz)"
                    % (qubit_lo / 1e9),
                }

                qubit_spec = QubitSpectroscopy(**qubit_spec_parameters)
                qubit_spec.setup_plot(**qubit_spec_plot_parameters)

                prof.run(qubit_spec)

        yoko = stage.YOKO
        # yoko.ramp(0e-3, yoko.level, 0.1e-3)
