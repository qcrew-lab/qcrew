'''
This script is used for only a qubit-cavity system and associated parameters

Parameters
----------
kerr : self-Kerr of cavity
chi  : cross-Kerr of qubit and cavity
anharm : self-Kerr of qubit

time_step : time step for the numerical pulse
'''

from qcrew.qcrew.measure.grape_ocp.grape.grape.pygrape import *
from qcrew.qcrew.measure.grape_ocp.helper.hamiltonians_setup import *
from qcrew.qcrew.measure.grape_ocp.helper.StateSetups import *

from qutip import *

# In GHz

kerr = -0e-6
chi = -0.6e-3
anharm = -0.0378

# Level truncations
qdim = 3
cdim = 10

# In ns
time_step = 2

# Save path

##########################################################


if __name__ == '__main__':
    
    # Making the pi pulse
    path = r'qcrew\measure\grape_ocp\Saved Pulse Sequences\pi_pulse'

    setups = SS.make_setups(
        cdim = cdim,
        qdim = qdim,
        target = 'pi_pulse',
    )
    
    init_ctrls = 0.5e-3 * random_waves(2, 200)

    penalties = [
        # To penalise amplitude
        make_amp_cost(1e-4, 2e-2, iq_pairs=False),
        # To penalise gradient for better bandwidth
        make_lin_deriv_cost(1e0, iq_pairs=False),
    ]

    opts = {
        "maxfun": 15000 * 5,
        "maxiter": 15000 * 5,
    }

    reporters = [
        print_costs(),                                                    # Default, prints fidelities
        save_waves(['QubitI', 'QubitQ',], 5),                   # Saves the waves as ".npz"
        plot_waves(['QubitI',' QubitQ', ], 5, iq_pairs = False),
                                                                                # Plots the waves, saves as pdf
        plot_trajectories(setups[0], 10),                         # Plots probability trajectories
        plot_states(10),
        plot_fidelity(10),                                               # Plots fidelity over iteration
        verify_from_setup(SS.make_setup(cdim+2, qdim), 10),
                                                                                # Consistency check
    ]

    result = run_grape(
        init_ctrls,
        setups,
        dt=time_step,
        save_data = 10,
        reporter_fns = reporters,
        penalty_fns = penalties,
        discrepancy_penalty=1e6,
        outdir = path,
        #freq_range = (-10e-3, 10e-3),
        #sigma_shape = 20,
        **opts
    )


    # Making the displacement pulse
    path = r'qcrew\measure\grape_ocp\Saved Pulse Sequences\coherent'

    setups = SS.make_setups(
        cdim = cdim,
        qdim = qdim,
        target = 'coherent',
    )
    
    init_ctrls = 0.5e-3 * random_waves(2, 200, 20)

    penalties = [
        # To penalise amplitude
        make_amp_cost(1e-4, 2e-2, iq_pairs=False),
        # To penalise gradient for better bandwidth
        make_lin_deriv_cost(1e-2, iq_pairs=False),
    ]

    opts = {
        "maxfun": 15000 * 5,
        "maxiter": 15000 * 5,
    }

    reporters = [
        print_costs(),                                                      # Default, prints fidelities
        save_waves(['CavityI', 'CavityQ',], 5),                             # Saves the waves as ".npz"
        plot_waves(['CavityI',' CavityQ', ], 5, iq_pairs = False),
                                                                            # Plots the waves, saves as pdf
        plot_trajectories(setups[0], 10),                                   # Plots probability trajectories
        plot_states(10),
        plot_fidelity(10),                                                  # Plots fidelity over iteration
        verify_from_setup(SS.make_setup(cdim+2, qdim), 10),
                                                                            # Consistency check
    ]

    result = run_grape(
        init_ctrls,
        setups,
        dt=time_step,
        save_data = 10,
        reporter_fns = reporters,
        penalty_fns = penalties,
        discrepancy_penalty=1e6,
        outdir = path,
        #freq_range = (-5e-3, 5e-3),
        #sigma_shape = 80,
        #n_proc = 2,
        **opts
    )



