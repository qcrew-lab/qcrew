'''
Holds the functions for retrieving and saving the data
and for data visualisation (plotting)

Last Update: Sept 2022 Kai Xiang
'''
import numpy as np
import matplotlib.pyplot as plt
from qutip import *
from Hamiltonians import *
from matplotlib.animation import FuncAnimation

def save(result, save_path, args):
    '''
    To save relevant information
    Parameters
    ---------
    result : pygrape result object
        Describes the result of optimsation
    save_path : string
        Desribes the directory to save the file (.npz)
    args : dict
        Contains the necessary miscellaneous parameters
    
    Returns
    ---------
    None
    '''
    
    if len(result.controls) == 4:
        np.savez(
            save_path,
            ts = result.ts,
            cav_X = result.controls[0],
            cav_Y = result.controls[1],
            qb_X = result.controls[2],
            qb_Y = result.controls[3],
            chi = args['chi'],
            anharm = args['anharm'],
            kerr = 0 if 'kerr' not in args else args['kerr'],
            c_dims = 8 if 'c_dims' not in args else args['c_dims'],
            q_dims = 2 if 'q_dims' not in args else args['q_dims'],
            p_len = args['p_len'],
            name = None if 'name' not in args else args['name'],
            targ_fid = args['targ_fid'],
        )
    elif len(results.controls) == 2:
        np.savez(
            save_path,
            ts = result.ts,
            pulseX = result.controls[0],
            pulseY = result.controls[1],
            qubit_freq = 0 if 'qubit_freq' not in args else args['qubit_freq'],
            cav_freq = 0 if 'cav_freq' not in args else args['cav_freq'],
            c_dims = 10 if 'c_dims' not in args else args['c_dims'],
            p_len = args['p_len'],
            name = None if 'name' not in args else args['name'],
            targ_fid = args['targ_fid'],
        )

    print(f"File saved at {save_path}")

def read_amplitudes_from_file(filename):
    """
    Reads file that contains a pulse amplitudes and retrieve it as array

    Parameters:
    ---------
    filename: string
        Name of the file where the pulse is stored.

    Returns:
    ---------
    amplitudes: ndarray
        Array of floats corresponding to pulse amplitudes.
    """

    if filename.split(".")[-1] == "txt":
        f = open(filename, "r")
        pulse_amplitudes = []
        f_lines = f.readlines()
        times = [float(line.split()[0]) for line in f_lines]
        pulse_amplitudes = [[float(line.split()[i]) for line in f_lines]
                            for i in range(1, len(f_lines[0].split()))]

    if filename.split(".")[-1] == "npz":
        f = np.load(filename)
        times = f["ts"]
        pulse_amplitudes = [f["cav_X"], f["cav_Y"],  f["qb_X"], f["qb_Y"]] if "cav_X" in f else [f["pulseX"], f["pulseY"]]
        args = {
            'chi': 0 if 'anharm' not in f else float(f['chi']),
            'kerr':  0 if 'anharm' not in f else float(f['kerr']),
            'anharm':  0 if 'anharm' not in f else float(f['anharm']),
            'c_dims':  10 if 'c_dims' not in f else int(f['c_dims']),
            'q_dims':  2 if 'q_dims' not in f else int(f['q_dims']),
            'p_len':  int(f['p_len']),
            'name': str(f['name']),
            'targ_fid':  float(f['targ_fid']),
            'qubit_freq' : 0 if 'qubit_freq' not in f else int(f['qubit_freq']),
            'cav_freq' : 0 if 'cav_freq' not in f else int(f['cav_freq']),
        }

    return np.array(times), np.array(pulse_amplitudes), args

def show_pulse(result = None, pulse_save_file = None):
    '''
    Plotting the Pulse waveform
    Parameters
    ---------
    result : pygrape result object
        Describes the result of pygrape optimisation
    pulse_save_file : string ('.npz')
        Save file of the calculated pulse waveform

    Returns
    ---------
    None
    '''
    if result != None:
        
        if len(result.controls) == 4:
            plt.plot(result.ts, result.controls[0], label = "Resonator Pulse X")
            plt.plot(result.ts, result.controls[1], label = "Resonator Pulse Y")
            plt.plot(result.ts, result.controls[2], "--", label = "Qubit Pulse X")
            plt.plot(result.ts, result.controls[3], "--", label = "Qubit Pulse Y")
            plt.legend()
            plt.grid()
            plt.title("Pulse Sequence in the Interaction Picture")
            plt.show()
            return

        if len(result.controls) == 2:
            plt.plot(result.ts, result.controls[0], label = "Pulse X")
            plt.plot(result.ts, result.controls[1], label = "Pulse Y")
            plt.legend()
            plt.grid()
            plt.title("Pulse Sequence in the Interaction Picture")
            plt.show()
            return
    
    if pulse_save_file != None:
        ts, amps, args = read_amplitudes_from_file(pulse_save_file)
        
        if len(amps) == 4:
            plt.plot(ts, amps[0], label = "Resonator Pulse X")
            plt.plot(ts, amps[1], label = "Resonator Pulse Y")
            plt.plot(ts, amps[2], "--", label = "Qubit Pulse X")
            plt.plot(ts, amps[3], "--", label = "Qubit Pulse Y")
            plt.legend()
            plt.grid()
            plt.title("Pulse Sequence in the Interaction Picture")
            plt.show()
            return
        
        if len(amps) == 2:
            plt.plot(ts, amps[0], label = "Pulse X")
            plt.plot(ts, amps[1], label = "Pulse Y")
            plt.legend()
            plt.grid()
            plt.title("Pulse Sequence in the Interaction Picture")
            plt.show()
            return

    raise Exception("No pulse provided - Pass a valid save file or a pygrape optimisation result object")

def get_AW_envelope(amplitudes, times,):
    '''
    Gets the wave envelope 

    Parameters
    ---------
    amplitudes : list of floats
        Describes the pulse
    times : list of floats
        Describes the time steps

    Returns
    ---------
    envelope : function
        Returns a function that gives the amplitude at time t
    '''
    if not len(times) == len(amplitudes):
        print("Both amplitudes and times arrays must have equal length")

    # Get time step. This assumes the step is constant.
    dt = times[1]-times[0]

    def envelope(t, args):
        if np.min(times)<t<np.max(times):
            return amplitudes[int(t//dt)]
        else:
            return 0
    return envelope

def show_evolution(result = None, args = None, pulse_save_file = None, save_path = None, initial = None, t_len = 1000, t_step = 0.1):
    '''
    To generate a gif of the wigner time evolution

    Parameters
    ---------
    result : pygrape result object
        Describes the result of pygrape optimisation
    args : dict
        Contains the miscellaneous parameters used
    initial : Qobj ket
        The initial state to evolve from. If None, the vacuum state is used
    t_len : float / int
        Total time to evolve for (in ns)
    t_step : float / int
        Time step to evolve for (in ns)
    pulse_save_file : string ('.npz')
        Save file of the calculated pulse waveform
    save_path : string
        Directory to save the gif to

    Returns
    ---------
    None
    '''
    if pulse_save_file != None and args is None:
        ts, amps, args = read_amplitudes_from_file(pulse_save_file)

    # Initial State
    if initial is None:
        initial = tensor(fock(args['c_dims'], 0), fock(args['q_dims'], 0))

        
    # Get the Hamiltonians
    H0, H_ctrl = make_Hamiltonian(args)
    H_targ = make_unitary_target(args)

    if result is not None:
        times, amplitudes = result.ts, result.controls
    else:
        times, amplitudes = ts, amps

    # Cavity Pulse
    envelope_quad1 = get_AW_envelope(amplitudes[0], times)
    H_res_quad1 = [H_ctrl[0], envelope_quad1]
    envelope_quad2 = get_AW_envelope(amplitudes[1], times)
    H_res_quad2 = [H_ctrl[1], envelope_quad2]

    # Qubit Pulse
    envelope_sx = get_AW_envelope(amplitudes[2], times)
    H_qubit_sx = [H_ctrl[2], envelope_sx]
    envelope_sy = get_AW_envelope(amplitudes[3], times)
    H_qubit_sy = [H_ctrl[3], envelope_sy]

    H = [H0, H_res_quad1, H_res_quad2, H_qubit_sx, H_qubit_sy]

    # Time steps
    t_list = np.arange(0, t_len, t_step)

    # ME Solver Output
    solved = mesolve(H, initial, t_list, options = Options(nsteps = 2000))

    # plot wigner function
    max_range = 6
    displ_array = np.linspace(-max_range, max_range, 61)
    wigner_list0 = [wigner(x.ptrace(0), displ_array, displ_array) for x in solved.states[::40]]
    wigner_list1 = [wigner(x.ptrace(1), displ_array, displ_array) for x in solved.states[::40]]

    # create first plot
    fig, axes = plt.subplots(1,2)
    axes[0].set_aspect('equal', 'box')
    axes[1].set_aspect('equal', 'box')
    fig.set_size_inches(20, 8)
    wigner_f0 = wigner(solved.states[0].ptrace(0), displ_array, displ_array)
    wigner_f1 = wigner(solved.states[0].ptrace(1), displ_array, displ_array)
    cont0 = axes[0].pcolormesh(displ_array, displ_array, wigner_f0, cmap = "bwr")
    cont1 = axes[1].pcolormesh(displ_array, displ_array, wigner_f1, cmap = "bwr")
    cb = fig.colorbar(cont0)

    # refresh function
    def animated_wigner(frame):
        wigner_f0 = wigner_list0[frame]
        wigner_f1 = wigner_list1[frame]
        cont0 = axes[0].pcolormesh(displ_array, displ_array, wigner_f0, cmap = "bwr")
        cont1 = axes[1].pcolormesh(displ_array, displ_array, wigner_f1, cmap = "bwr")
        cont0.set_clim(-1/np.pi, 1/np.pi)
        cont1.set_clim(-1/np.pi, 1/np.pi)

        axes[0].set_title("Cavity State", fontsize = 20)
        axes[1].set_title("Qubit State", fontsize = 20)


    anim = FuncAnimation(fig, animated_wigner, frames=len(wigner_list0), interval=100)

    if save_path == None:
        return
    anim.save(save_path, writer='imagemagick')

def show(result = None, args = None, pulse_save_file = None, initial = None, t_len = 1000, t_step = 0.1):
    '''
    To generate a plot of the photon number time evolution

    Parameters
    ---------
    result : pygrape result object
        Describes the result of pygrape optimisation
    args : dict
        Contains the miscellaneous parameters used
    initial : Qobj ket
        The initial state to evolve from. If None, the vacuum state is used
    t_len : float / int
        Total time to evolve for (in ns)
    t_step : float / int
        Time step to evolve for (in ns)
    pulse_save_file : string ('npz')
        Save file of pulse waveform

    Returns
    ---------
    None
    '''
    if args == None and pulse_save_file != None:
        ts, amps, args = read_amplitudes_from_file(pulse_save_file)

    c_dims = 8 if 'c_dims' not in args else args['c_dims']
    q_dims = 2 if 'q_dims' not in args else args['q_dims']

    # Initial State
    if initial is None:
        initial = tensor(fock(args['c_dims'], 0), fock(args['q_dims'], 0))

    # Time steps
    t_list = np.arange(0, t_len, t_step)

    a = tensor(destroy(c_dims), qeye(q_dims))
    b = tensor(qeye(c_dims), destroy(q_dims))

    # Get the Hamiltonians
    H0, H_ctrl = make_Hamiltonian(args)

    if result is not None:
        times, amplitudes = result.ts, result.controls
    else:
        times, amplitudes = ts, amps

    # Cavity Pulse
    envelope_quad1 = get_AW_envelope(amplitudes[0], times)
    H_res_quad1 = [H_ctrl[0], envelope_quad1]
    envelope_quad2 = get_AW_envelope(amplitudes[1], times)
    H_res_quad2 = [H_ctrl[1], envelope_quad2]

    # Qubit Pulse
    envelope_sx = get_AW_envelope(amplitudes[2], times)
    H_qubit_sx = [H_ctrl[2], envelope_sx]
    envelope_sy = get_AW_envelope(amplitudes[3], times)
    H_qubit_sy = [H_ctrl[3], envelope_sy]
    H = [H0, H_res_quad1, H_res_quad2, H_qubit_sx, H_qubit_sy]

    H_targ = make_unitary_target(args)
    solved = mesolve(H, initial, t_list, options = Options(nsteps = 2000))

    cavity_expectation = [ (state.dag() * a.dag()*a * state)[0,0] for state in solved.states ]
    qubit_expectation = [ (state.dag() * b.dag()*b * state)[0,0] for state in solved.states ]

    plt.plot(t_list, cavity_expectation, label = "Cavity")
    plt.plot(t_list, qubit_expectation, label = "Qubit")
    plt.title("Expectation of Photon Number Operator")
    plt.legend()
    plt.show()