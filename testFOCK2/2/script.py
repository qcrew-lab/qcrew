from pygrape import *
from qutip import *
from qutip.qip.device import Processor

import numpy as np
import matplotlib.pyplot as plt

save_path = 'testFOCK2'
make_gif = 0

args = dict(
    # Hamiltonian Parameters (in GHz)
    anharm = -211.9e-3,
    kerr = -0e-6,
    chi = -0.585e-3,
    qdim = 3,
    cdim = 8,

    wq = 5.26634,
    wc = 6.13675,
    
    # Pulse Parameters
    num_points = 1600,
    init_drive_scale = 1e-4,
    dt = 1.0,                  # in ns
    
    # Penalties
    make_amp_cost_args = (1e-4, 1e-2),
    make_lin_amp_cost_args = None,
    make_deriv_cost_args = None,
    make_lin_deriv_cost_args = (1e2,),
    
    # max iterations
    discrepancy_penalty = 1e6,
    freq_range = None,
    shape_sigma = 40, 
    bound_amp = None,
    targ_fid = 1 - 1e-2,

		# Trying to include gauge freedoms 
    #gauge_ops = ['phase',], 
    #init_aux_params = [1,],
    # Looks like it wasn't implemented

    # Approximations
    use_taylor = True,
    sparse = True,
    taylor_order = 20,
    
    # Type of pulse
    target = 'fock',
    param = 2,       # Key parameter associated with target, e.g., displacement, etc.  
    )

def make_Hamiltonian(cdim, qdim, anharm = -0.0378, kerr = -1e-6,chi = -0.6e-3,):
    # Operators
    q = tensor(qeye(cdim), destroy(qdim))
    qd = q.dag()
    c = tensor(destroy(cdim), qeye(qdim))
    cd = c.dag()

    # Hamiltonian
    H0 =  anharm/2 * qd*qd*q*q
    H0 += kerr/2 * cd*cd*c*c
    H0 += chi *cd*c*qd*q
    H0 *= 2 * np.pi

    # Control Hamiltonians
    Hc = [
        2*np.pi*(c + cd),
        1j*2*np.pi*(c - cd),
        2*np.pi*(q + qd),
        1j*2*np.pi*(q - qd),
        ]

    return H0, Hc

def make_setup(
    cdim, qdim, target = 'pi_pulse',
    anharm = 0, kerr = 0e-6, chi = 0e-3,
    param = 0, use_taylor = False,
    sparse = False, taylor_order = 20,
    gauge_ops = None):
    
    H0, Hc = make_Hamiltonian(cdim, qdim, anharm = anharm, chi = chi, kerr = kerr)

    init, final = None, None

    if target == 'fock':
        init = [tensor(
            fock(cdim, 0), basis(qdim,0)
            )]
        final = [tensor(
            fock(cdim, param), basis(qdim,0)
            )]
        
    elif target == 'coherent':
        init = [tensor(
            fock(cdim, 0), basis(qdim,0)
            )]
        final = [tensor(
            coherent(cdim, param), basis(qdim,0)
            )]

        Hc = Hc[:2]
        
    elif target == 'pi_pulse':
        init = [tensor(
            fock(cdim, 0), basis(qdim,0)
            )]
        final = [tensor(
            fock(cdim, 0), basis(qdim,1)
            )]

        Hc = Hc[2:]

    
    elif target == 'fock_12':
        init = [tensor(
            fock(cdim, 0), basis(qdim,0)
            )]
        final = [tensor(
            fock(cdim, 1) / np.sqrt(2) + fock(cdim, 2) / np.sqrt(2), basis(qdim,0)
            )]

    elif target == 'hadamard_coherent':
        init = [
            tensor(coherent(cdim, param), basis(qdim, 0)),
            tensor(coherent(cdim, -param), basis(qdim, 0)),
            ]

        final = [
            tensor((coherent(cdim, param) + coherent(cdim, -param))/np.sqrt(2), basis(qdim, 0)),
            tensor((coherent(cdim, param) - coherent(cdim, -param))/np.sqrt(2), basis(qdim, 0)),
            ]

        """
        U = ( coherent(cdim, param) + coherent(cdim, -param) ) * coherent(cdim, param).dag() /np.sqrt(2)
        U+= ( coherent(cdim, param) - coherent(cdim, -param) ) * coherent(cdim, -param).dag() /np.sqrt(2)

        U = tensor(U, qeye(qdim))

        setup = UnitarySetup(
            H0, Hc,
            U,
            )
        
        return setup
        """

    else:
        raise Exception("Please provide a valid state target")

    # Making Gauge Operator for phase degree of freedom
    guage_operators = []
    
    if gauge_ops == None:
        gauge_ops = []
        
    for op in gauge_ops:
        if op == 'phase':
            number_op = fock(cdim, 1) * fock(cdim, 1).dag()
            number_op = tensor(number_op, qeye(qdim))
            
            phase_op = (1j * number_op).expm()
            guage_operators += [phase_op,]

    # Was not implemented, heck it
    
    setup = StateTransferSetup(
        H0, Hc,
        init, final,
        use_taylor = use_taylor,
        sparse = sparse,
        gauge_ops = guage_operators,
        )

    setup.taylor_order = taylor_order

    return setup

def make_setups(**args):
    setup1 = make_setup(**args)

    args['cdim'] += 1
    setup2 = make_setup(**args)
    
    return [setup1, setup2]

if __name__ == "__main__":
    target = args['target']
    # Make the setups
    setups = make_setups(
        cdim = args['cdim'],
        qdim = args['qdim'],
        target = target,
        anharm = args['anharm'],
        kerr = args['kerr'],
        chi = args['chi'],
        param = args['param'],
        use_taylor = args['use_taylor'],
        taylor_order = args['taylor_order'],
        sparse = args['sparse'],
        #gauge_ops = args['gauge_ops'],
        )

    # Initialise pulses
    num_ctrls = 2 if target == 'pi_pulse' or target == 'coherent' else 4
    init_ctrls = args['init_drive_scale'] * random_waves(num_ctrls, args['num_points'])
    dt = args['dt']

    # Reporter functions

    pulse_names = ['CavityI', 'CavityQ','QubitI', 'QubitQ',]

    if target == 'pi_pulse': pulse_names = pulse_names[2:]
    if target == 'coherent': pulse_names = pulse_names[:2]
    
    reporters = [
            print_costs(),                                                    # Default, prints fidelities
            save_waves(pulse_names, 5),
                                                                                    # Saves the waves as ".npz"
            plot_waves(pulse_names, 5, iq_pairs = False),
                                                                                    # Plots the waves, saves as pdf
            plot_trajectories(setups[0], 10),
                                                                                    # Plots probability trajectories
            plot_states(10),
            plot_fidelity(10),                                               # Plots fidelity over iteration
            verify_from_setup(
                make_setup(
                    cdim = args['cdim'],
                    qdim = args['qdim'],
                    target = target,
                    anharm = args['anharm'],
                    kerr = args['kerr'],
                    chi = args['chi'],
                    param = args['param'],
                    use_taylor = args['use_taylor'],
                    taylor_order = args['taylor_order'],
                    sparse = args['sparse'],
                    #gauge_ops = args['gauge_ops'],
                    ),
                              10),
                                                                                    # Consistency check for higher fock trunctions
            save_script(__file__)
        ]

    # Penalty functions
    penalties = []

    if args['make_amp_cost_args'] != None:
        # To penalise amplitude to a soft threshold
        penalties += [make_amp_cost(*args['make_amp_cost_args'], iq_pairs=False),]

    if args['make_lin_amp_cost_args'] != None:
        # To penalise amplitude to a low number
        penalties += [make_lin_amp_cost(*args['make_lin_amp_cost_args'], iq_pairs=False),]
    
    if args['make_deriv_cost_args'] != None:
        # To penalise gradient for better bandwidth to a soft threshold
        penalties += [make_deriv_cost(*args['make_deriv_cost_args'], iq_pairs=False),]
    
    if args['make_lin_deriv_cost_args'] != None:
        # To penalise gradient for better bandwidth
        penalties += [make_lin_deriv_cost(*args['make_lin_deriv_cost_args'], iq_pairs=False),]

    # Additional Parameters
    opts = {
        "maxfun": 15000 * 5,
        "maxiter": 15000 * 5,
    }


    # Run grape
    result = run_grape(
        init_ctrls,
        setups,
        dt=dt,
        term_fid = args['targ_fid'],
        save_data = 10,
        reporter_fns = reporters,
        penalty_fns = penalties,
        discrepancy_penalty=args['discrepancy_penalty'],
        n_proc = 2,
        outdir = save_path,
        freq_range = args['freq_range'],
        shape_sigma = args['shape_sigma'],
        bound_amp = args['bound_amp'],
        #init_aux_params = args['init_aux_params'],
        **opts,
        )

    #########################################################
    # To show pulse plots

    if make_gif:
        cdim = args['cdim']
        qdim = args['qdim']
        H0, Hc = make_Hamiltonian(cdim, qdim, anharm = args['anharm'],
                                  chi = args['chi'], kerr = args['kerr'])

        processor = Processor(
            N=2,                                   # Number of component systems
            spline_kind="cubic",            # Interpolation for pulses
            dims = [cdim, qdim,],
            )

        processor.add_control(Hc[0], targets = [0,1], label = 'Cavity X-pulse')
        processor.add_control(Hc[1], targets = [0,1], label = 'Cavity Y-pulse')
        processor.add_control(Hc[2], targets = [0,1], label = 'Qubit X-pulse')
        processor.add_control(Hc[3], targets = [0,1], label = 'Qubit Y-pulse')
        processor.add_drift(H0, targets = [0,1])
        processor.pulses[0].tlist = result.ts
        processor.pulses[0].coeff = result.controls[0]
        processor.pulses[1].tlist = result.ts
        processor.pulses[1].coeff = result.controls[1]
        processor.pulses[2].tlist = result.ts
        processor.pulses[2].coeff = result.controls[2]
        processor.pulses[3].tlist = result.ts
        processor.pulses[3].coeff = result.controls[3]
        processor.plot_pulses()

        plt.show()

        sim_result = processor.run_state(
            init_state = tensor(fock(cdim,0), basis(qdim,0)),
            solver = 'mesolve',
            )

        #show_bloch(sim_result)
        #show_wigner(sim_result)
        show_evolution(sim_result, savepath = save_path)
