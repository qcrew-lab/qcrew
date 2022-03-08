"""
A python class describing a qubit spectroscopy using QM for different values of
current in a current source.
This class serves as a QUA script generator with user-defined parameters.
"""

from qcrew.control import professor as prof
from qcrew.control import Stagehand

from qcrew.measure.qubit_experiments_GE.qubit_spec import QubitSpectroscopy
from qcrew.measure.resonator_characterization.rr_spec import RRSpectroscopy

import numpy as np
import h5py

# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    current_start = 10e-3
    current_stop = -10.1e-3
    current_step = -0.5e-3
    current_sweep = np.arange(current_start, current_stop, current_step)

    qubit_lo_start = 5.42733e9
    qubit_lo_stop = 4e9
    qubit_lo_step = -200e6
    qubit_lo_sweep = np.arange(qubit_lo_start, qubit_lo_stop, qubit_lo_step)

    # Store information in lists to print later
    filename_list = []
    current_list = []
    lo_list = []
    rr_if_list = []

    for current in current_sweep:

        # Change value of current source
        with Stagehand() as stage:
            yoko = stage.YOKO
            yoko.source = "current"
            yoko.level = current  # set output to nominal value
            yoko.state = True

        # Find resonator resonant frequency
        ## Do RR spectroscopy
        x_start = -56e6
        x_stop = -46e6
        x_step = 0.05e6

        rr_spec_parameters = {
            "modes": ["RR"],
            "reps": 10,
            "wait_time": 10000,
            "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
            "fit_fn": None,
        }

        rr_spec_plot_parameters = {
            "xlabel": "Resonator pulse frequency (Hz)",
        }

        rr_spec = RRSpectroscopy(**rr_spec_parameters)
        rr_spec.setup_plot(**rr_spec_plot_parameters)

        prof.run(rr_spec)

        ## Get frequency of MAXIMUM transmission (transmission measurement)
        filepath = rr_spec.filename
        data = h5py.File(filepath, "r")["data"]
        z_avg = np.array(data["Z_AVG"])
        frequencies = np.array(data["x"])
        rr_if = frequencies[np.argmax(z_avg)]
        ## Change RR IF accordingly

        with Stagehand() as stage:
            rr = stage.RR
            rr.int_freq = float(rr_if)

        # proceed with qubit spectroscopy
        for qubit_lo in qubit_lo_sweep:

            with Stagehand() as stage:
                qubit = stage.QUBIT
                qubit.lo_freq = qubit_lo

            x_start = -200e6
            x_stop = 0e6
            x_step = 0.5e6

            qubit_spec_parameters = {
                "modes": ["QUBIT", "RR"],
                "reps": 10,
                "wait_time": 100000,
                "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                "qubit_op": "constant_pulse",
                "fit_fn": None,
            }

            qubit_spec_plot_parameters = {
                "xlabel": "Qubit pulse frequency (Hz) (LO = %.3f GHz)"
                % (qubit_lo / 1e9),
            }

            qubit_spec = QubitSpectroscopy(**qubit_spec_parameters)
            qubit_spec.setup_plot(**qubit_spec_plot_parameters)

            prof.run(qubit_spec)

            filename_list.append(qubit_spec.filename)
            current_list.append(current)
            lo_list.append(qubit_lo)
            rr_if_list.append(rr_if)

            with Stagehand() as stage:
                yoko = stage.YOKO
                yoko.state = False

            # Retrieve the saved data
            file = h5py.File(qubit_spec.filename, "r")
            z_avg = np.array(data["Z_AVG"])

            ## Correct floor of z_avg
            z_avg -= np.average(z_avg)
            z_avg = list(z_avg)
            if current_step < 0:
                z_avg.reverse()

            ## Get frequencies
            freqs = np.array(data["x"]) + qubit_lo
            freqs = list(freqs)
            if current_step < 0:
                freqs.reverse()

    for i, filename in enumerate(filename_list):
        print("Experiment number %d: " % i)
        print("    qubit lo = %.8f GHz" % (lo_list[i] / 1e9))
        print("    current  = %.2f mA" % (current_list[i] / 1e-3))
        print("    rr IF    = %.3f MHz" % (rr_if_list[i] / 1e6))
        print(filename)
