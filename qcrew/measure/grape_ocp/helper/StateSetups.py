from qcrew.qcrew.measure.grape_ocp.grape.grape.pygrape import *
from qutip import *

import numpy as np

from hamiltonians_setup import *

def make_pi_pulse(cdim, qdim):
    '''
    Makes a pi-pulse unitary from ground state
    '''
    
    inits = [
        tensor(fock(cdim,0), basis(qdim,0))
        ]

    finals = [
        tensor(fock(cdim,0), basis(qdim,1))
        ]
    
    return inits, finals

def make_coherent(cdim, qdim, alpha = 1):
    '''
    Makes a coherent state unitary from ground state
    '''

    inits = [
        tensor(fock(cdim,0), basis(qdim,0))
        ]

    finals = [
        tensor(coherent(cdim,alpha), basis(qdim,0))
        ]

    return inits, finals

def make_fock(cdim, qdim, fock_n = 1):
    '''
    Makes a fock state unitary from ground state
    '''

    inits = [
        tensor(fock(cdim,0), basis(qdim,0))
        ]

    finals = [
        tensor(fock(cdim,fock_n), basis(qdim,0))
        ]

    return inits, finals

def make_setup(\
    cdim=8, qdim=2, target = 'fock',\
    alpha = 1, anharm = -0.1, kerr = -1e-6, chi = -1e-3, fock_n = 1):
    '''
    Makes two StateTransferSetup Classes with different Fock truncations to ensure consistency

    Parameters
    -------------
    cdim : int
        Truncation for Fock levels

    qdim : int
        Dimensions of qubit (or qutrit)

    target : string
        The target unitary

    args : Other stuff
        anharmonicity
        kerr
        chi
        alpha
        fock_n

    Returns
    ----------
    List(StateTransferSetup, ... )
    '''
    S_args = dict()
    S_fn = None

    if target == 'fock':
        S_args[fock_n] = fock_n
        S_fn = make_fock
    elif target == 'coherent':
        S_args[alpha] = alpha
        S_fn = make_coherent
    elif target == 'pi_pulse':
        S_fn = make_pi_pulse

    H_args = dict(
        anharm = anharm,
        kerr = kerr,
        chi = chi
        )

    H0, Hc = make_Hamiltonian(cdim, qdim, **H_args)

    if target == 'coherent':
        Hc = Hc[:2]
    if target == 'pi_pulse':
        Hc = Hc[2:]

    setup = StateTransferSetup(
        H0, Hc,
        *S_fn(cdim, qdim, *S_args)
        )

    return setup

def make_setups(**args):
    '''
    To make multiple setups
    '''
    setup1 = make_setup(**args)

    args['cdim'] += 1
    setup2 = make_setup(**args)
    
    return [setup1, setup2]
