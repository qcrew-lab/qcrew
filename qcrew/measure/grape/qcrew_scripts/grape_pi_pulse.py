""" """
from pathlib import Path
import numpy as np
from datetime import datetime
from qcrew.control import Stagehand
from qcrew.control.pulses import IQPulse

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

from qutip import destroy, basis
from pygrape import *

DRIVE = 1e-3


def make_qubit_cal_setup(q_dim=2, alpha=0.0, mask=[1, 1]):
    a, ad = destroy(q_dim), destroy(q_dim).dag()

    if alpha == 0:
        H0 = a.full() * 0
    else:
        H0 = 0.5 * alpha * a.dag() * a.dag() * a * a

    I = a + ad
    Q = 1j * (a - ad)
    drives = [I.full() * mask[0], Q.full() * mask[1]]
    Hcs = 2 * np.pi * DRIVE * np.array(drives)

    in_states = [
        basis(q_dim, 0),
    ]
    out_states = [
        basis(q_dim, 1),
    ]

    return StateTransferSetup(
        2 * np.pi * H0, Hcs, in_states, out_states, gauge_ops=None
    )


class GrapePiPulse(Experiment):

    name = "GrapePiPulse"

    def __init__(self, oct_op, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.oct_op = oct_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        # generate state
        qubit.play(self.oct_op, ampx=self.x)
        qua.align(qubit.name, rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # # wait system reset
        qua.wait(int(self.wait_time // 4), qubit.name)
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    date = datetime.now().strftime("%Y%m%d")
    # generate pulse with run_grape if needed
    outdir = Path(f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/oct_pulses/pi/20220615")
    outdir.mkdir(exist_ok=True)
    pnames = ["qI", "qQ"]

    generate_pulse = False
    play_pulse = True

    if generate_pulse:
        plen = 80
        alpha = -0.195

        setup = make_qubit_cal_setup(q_dim=2, alpha=alpha)

        init_ctrls = np.ones((len(pnames), plen))

        reporters = [
            print_costs(),
            save_waves(pnames, 5),
            plot_waves(pnames, 5),
        ]

        results = run_grape(
            init_ctrls,
            setup,
            reporter_fns=reporters,
            outdir=outdir,
            maxiter=500,
            dt=2,
            save_data=10,
            term_fid=0.999,
            bound_amp=0.25,
        )

    # loading pulse generated by run_grape
    index = 4
    file = outdir / f"{index}/waves.npz"
    npzfile = np.load(file)
    iwave, qwave = npzfile[pnames[0]], npzfile[pnames[1]]

    scaling_factor = 0.25
    iwave *= scaling_factor
    qwave *= scaling_factor

    if play_pulse:

        with Stagehand() as stage:
            qubit = stage.QUBIT

            qubit.operations = {"oct_pulse": IQPulse(i_wave=iwave, q_wave=qwave)}

            amp_start = -1
            amp_stop = 1
            amp_step = 0.05

            parameters = {
                "modes": [qubit, stage.RR],
                "reps": 50000,
                "wait_time": 100000,
                "fetch_period": 1,  # time between data fetching rounds in sec
                "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
                "oct_op": "oct_pulse",
                "fit_fn": "sine",
                "single_shot": True,
            }

            plot_parameters = {
                "xlabel": "Amplitude scaling factor",
                "ylabel": "Signal (AU)",
            }

            experiment = GrapePiPulse(**parameters)
            experiment.setup_plot(**plot_parameters)

            # use this to play pulse with datasaving and plotting
            prof.run_with_stage(experiment, stage)

            # use this to play pulse without datasaving and plotting
            # qm_job = stage.QM.execute(experiment.QUA_sequence())

            qubit.remove_operation("oct_pulse")
