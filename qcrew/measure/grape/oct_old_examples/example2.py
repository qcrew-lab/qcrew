# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 13:51:03 2015

@author: rsl
"""

from pygrape.grape import run_grape, run_setup
from pygrape.penalties import make_amp_cost, make_deriv_cost, make_l1_penalty
from pygrape.preparations import random_waves
from pygrape.reporters import *
from pygrape.setups import StateTransferSetup, UnitarySetup

import qutip
from qutip import tensor, qeye, sigmaz, sigmax, sigmay, destroy, basis, coherent

import numpy as np
from numpy import pi
import matplotlib.pyplot as plt

import itertools
import random
import time


c_dim = 11

def get_IQ_id(name):
    return [name+'I', name+'Q']

DRIVE = 1e-3

FILT_FUNC = lambda fs: np.exp(-fs**2/(2*0.250**2))

def make_as(c_dim, q_dim, num_qubits=1):
    '''
    Create creation and annihilation operators for a hilbert space of one
    cavity followed by an arbitrary number of qubits, in that order.
    
    Since all of the operators derive from this, this sets the Hilbert space
    structure. 
    '''
    annis = [destroy(c_dim),] + [qeye(c_dim),]*num_qubits
    for dimidx in range(num_qubits):
        for aidx, a in enumerate(annis):
            if dimidx + 1 == aidx:
                annis[aidx] = tensor(a, destroy(q_dim))
            else:
                annis[aidx] = tensor(a, qeye(q_dim))
                
    adags = [a.dag() for a in annis]
    return annis, adags
    
def make_hmt(chis, alphas, chi_primes, num_qubits=1, 
             c_dim=c_dim, q_dim=2, herm=False, 
             cav_exclusion=0, detunings=None):

    a, ad = make_as(c_dim, q_dim)
    
    num_ops = [x*y for x,y in zip(ad, a)]
    alpha_ops = [x*x*y*y for x,y in zip(ad, a)]

    H0 = 0*num_ops[0]  #QObj initialization 
    
    for idx1 in range(num_qubits+1):
        for idx2 in range(num_qubits+1):
            if idx2 <= idx1:
                continue
            H0 += chis[idx1, idx2] * num_ops[idx1] * num_ops[idx2]

    for alpha, op in zip(alphas, alpha_ops):
        H0 += 0.5*alpha*op
        
    if not (detunings is None):
        for det, op in zip(detunings, num_ops):
            H0 += det*op        
            
    for xp, op  in zip(chi_primes, num_ops):
        H0 += 0.5 * xp * op * ad[0] * ad[0] * a[0] * a[0]
        
    if herm:
        return 2 * pi * H0.full()     
        
    if 0:
        #If we're not hermitian, get the projectors onto the highest cavity 
        #number states.  
        dim = c_dim * q_dim**num_qubits
        nh = np.zeros(dim, dtype=np.complex)
        
        nh[-q_dim**num_qubits:] = -1j
        return 2 * pi * H0.full() + nh
        
    if 1:
        #Here we've used the new loss mechanism, not the original non-hermitian method
        dim = c_dim * q_dim**num_qubits
        nh = np.ones(dim, dtype=np.complex)  
        
        #FACTOR = 1 #1
        if cav_exclusion:
            nh[-cav_exclusion * q_dim**num_qubits:] = 0
    
        return 2 * pi * H0.full(), nh
        
    raise Exception
    
def make_drives(c_dim=c_dim, q_dim=2, mask=None, num_qubits=1):
    '''
    This assumes drives on ALL modes by default.  To only drive some modes,
    make a mask, e.g. [1,0,0,1] drives only the first mode (the cavity), and 
    the fourth mode, which is the third qubit.
    '''
    if mask is None:
        mask = [1,] * (1+num_qubits)
        
    a, ad = make_as(c_dim, q_dim)

    outs = []
    for include, op, opd in zip(mask, a, ad):
        if include:
            I = (op + opd)
            Q = 1j * (op - opd)
            outs.extend([I.full(), Q.full(),])
        
    return 2 * pi * DRIVE * np.array(outs)
    
def make_cav_drives(c_dim=c_dim, q_dim=2, mask=None, num_qubits=1):
    '''
    This assumes drives on ALL modes by default.  To only drive some modes,
    make a mask, e.g. [1,0,0,1] drives only the first mode (the cavity), and 
    the fourth mode, which is the third qubit.
    '''
    if mask is None:
        mask = [1,] * (1+num_qubits)
        
    a, ad = make_as(c_dim, q_dim)

    outs = []
    op, opd = a[0], ad[0]

    I = (op + opd)
    Q = 1j * (op - opd)
    outs.extend([I.full(), Q.full(),])
        
    return 2 * pi * DRIVE * np.array(outs)


    
def make_gauge_ops(c_dim=c_dim, q_dim=2, cavity_gauge=False, num_qubits=1,
                   ent_phase=False, mega=False,
                   max_cdim=22):
    '''
    We don't care about:
        Single qubit phase on the ancilla (Does the state-state formalism
            already remove this phase?)
        Single qubit phases on the register qubits
        (Single qubit ROTATIONS on the register qubits?)
        Phases on the cavity (Does this make sense if we always go 0->0?)
        
    '''
    assert q_dim == 2  #Requires generalized sigmaZ for higher qubit dims

 
    dn = qutip.basis(2,0) * qutip.basis(2,0).dag()
    up = qutip.basis(2,1) * qutip.basis(2,1).dag()
            
    Hgs = []
    HgA =  tensor(qeye(c_dim), sigmaz())
    Hgs.append(HgA)
    
    if mega:
        for i in range(max_cdim):
            for j in range(i + 1):
                op = np.zeros((c_dim,c_dim), dtype=np.complex)
                op[i,j] = 1.0
                op[j,i] = 1.0

#                Hgs.append(qutip.tensor(qutip.Qobj(op), qutip.qeye(q_dim)))
                Hgs.append(qutip.tensor(qutip.Qobj(op), up))
                Hgs.append(qutip.tensor(qutip.Qobj(op), dn))     
                
                if i != j:
                    op[i,j] = 1.0j
                    op[j,i] = -1.0j
                    
#                    Hgs.append(qutip.tensor(qutip.Qobj(op), qutip.qeye(q_dim)))      
                    Hgs.append(qutip.tensor(qutip.Qobj(op), up))      
                    Hgs.append(qutip.tensor(qutip.Qobj(op), dn))     
        
        
        
        
    elif cavity_gauge:
        if ent_phase:

            
            op = tensor(qutip.num(c_dim), dn) +  tensor(qutip.qeye(c_dim), up)
            Hgs.append(op)

            op = tensor(qutip.num(c_dim), up) +  tensor(qutip.qeye(c_dim), dn)
            Hgs.append(op)            
        
        else:
            Hgs.append(tensor(qutip.num(c_dim), qeye(q_dim)))
        
    
        
        
    return [Hg.full() for Hg in Hgs]


    

def make_setup(H, make_target, c_dim=c_dim, q_dim=2, 
               drive_mask=None, 
               hmt_kwargs={'cav_exclusion':0}, 
               gauge_kwargs={},
               target_kwargs={},
               setup_kwargs={}, 
               do_gauge=True, cavity_gauge=False,
               time_gauge=False):
    '''
    Generates H, controls, initial and target states, and gauge ops. 
    Returns grape setup
    '''
    H0, loss_vec = make_hmt(H[0], H[1], H[2], c_dim=c_dim, q_dim=q_dim, **hmt_kwargs)
    Hcs = make_drives(c_dim=c_dim, q_dim=q_dim, mask=drive_mask)
    in_states, out_states = make_target(c_dim=c_dim, **target_kwargs)
    if do_gauge:
        Hgs = make_gauge_ops(c_dim=c_dim, q_dim=q_dim, cavity_gauge=cavity_gauge, **gauge_kwargs)
        
        if time_gauge:
            Hgs = [-1 * H0,] + Hgs #Must be in this order
    else:
        Hgs = None
        
    setup = StateTransferSetup(H0, Hcs, in_states, out_states, gauge_ops=Hgs,
                              loss_vec=loss_vec, sparse=False,
                              use_taylor=False, **setup_kwargs)
    return setup


def make_qubit_cal_setup(q_dim=2, alpha=0.0, mask=[1,1]):
    a, ad = destroy(q_dim), destroy(q_dim).dag()

    if alpha == 0:
        H0 = a.full()*0
    else:
        H0 = 0.5 * alpha * a.dag() * a.dag() * a * a
    
    I = (a + ad)
    Q = 1j * (a - ad)
    drives = [I.full()*mask[0], Q.full()*mask[1]]
    Hcs = 2 * pi * DRIVE * np.array(drives)
    
    in_states = [basis(q_dim, 0),]
    out_states = [basis(q_dim, 1),]
    
    return StateTransferSetup(2*pi*H0, Hcs, in_states, out_states, gauge_ops=None)
    
def make_cav_cal_setup(c_dim=15, alpha=-7.5e-6, nbar=5, mask=[1,1]):
    a, ad = destroy(c_dim), destroy(c_dim).dag()

    if alpha == 0:
        H0 = a.full()*0
    else:
        H0 = 0.5 * alpha * a.dag() * a.dag() * a * a
    
    I = (a + ad)
    Q = 1j * (a - ad)
    drives = [I.full()*mask[0], Q.full()*mask[1]]
    Hcs = 2 * pi * DRIVE * np.array(drives)
    
    in_states = [basis(c_dim, 0),]
    out_states = [coherent(c_dim, np.sqrt(nbar)),]
    
    return StateTransferSetup(2*pi*H0, Hcs, in_states, out_states, gauge_ops=None)


if 0: # unitary setups for correction pulses

    def embed_op_largerH(op, target_dim):
        '''
        embed op in a larger Hilbert space
        '''
        Utarget = np.matrix(np.zeros((target_dim, target_dim), dtype=np.complex))
        Utarget[:op.shape[0],:op.shape[1]] = op
        return qutip.Qobj(Utarget)        
        
    def get_cavity_unitary(phases, c_dim=c_dim, q_dim=2):
        U_qubit = qeye(q_dim)
        
        phases = np.array(phases)
        theta = np.sqrt(phases.dot(phases)) # magnitude of rotation
        if theta == 0:
            theta = 0
            unit_vector = [0,0,0]
        else:
            unit_vector = phases / theta # unit vector specifying rotation
        sn = [sigmax(), sigmay(), sigmaz()]
        sn = [np.matrix(s.full()) for s in sn]
        n_dot_sigma = np.matrix(np.sum(nu * s for nu,s in zip(unit_vector, sn)))
        Id = np.matrix(qeye(2).full())
        U_cav = np.cos(theta) * Id - 1j* np.sin(theta) * n_dot_sigma
        U_cav = embed_op_largerH(U_cav, c_dim)
        
        return tensor(U_cav, U_qubit)

    def make_cavity_U_target(phases=[0,0,0], c_dim=c_dim, q_dim=2):  
    
        in_states = [
            tensor( basis(c_dim, 0), basis(q_dim,0)),
            tensor( basis(c_dim, 1), basis(q_dim,0)),
            ]    
        Un = get_cavity_unitary(phases, c_dim, q_dim)
        out_states = [ Un * s for s in in_states]
        
        return in_states, out_states 

def get_fock_ge(c_dim=c_dim, alpha=None, ret_vac=False, qbt=0):
    g = tensor(basis(c_dim,  0), basis(2,qbt))
    e = tensor(basis(c_dim,  1), basis(2,qbt)) 
            
    if not ret_vac:
        return g,e
    
    vac = tensor(coherent(c_dim,0), basis(2,qbt))
    return g,e, vac

def get_cat_ge(c_dim=c_dim, alpha=None, ret_vac=False, qbt=0):
    cat_g = tensor(coherent(c_dim,     alpha), basis(2,qbt)) + \
            tensor(coherent(c_dim,  -1*alpha), basis(2,qbt))
    cat_e = tensor(coherent(c_dim,  1j*alpha), basis(2,qbt)) + \
            tensor(coherent(c_dim, -1j*alpha), basis(2,qbt))
            
    if not ret_vac:
        return cat_g.unit(), cat_e.unit()
    
    vac = tensor(coherent(c_dim,0), basis(2,qbt))
    return cat_g.unit(), cat_e.unit(), vac


def get_kitten_ge(c_dim=23, ret_vac=False, qbt=0):
    '''
    g = fock(2)
    e = (fock(0) + fock(4)) / sqrt(2)
    '''
    g = tensor(basis(c_dim,  2), basis(2,qbt)) 
    e = tensor(basis(c_dim,  0), basis(2,qbt)) + \
        tensor(basis(c_dim,  4), basis(2,qbt))
    e = e.unit()
    
    if not ret_vac:
        return g, e
    
    vac = tensor(basis(c_dim,0), basis(2,qbt))
    return g, e, vac


#def get_make_target_func(func, get_ge):
#    def wrapper(**kwargs):
#        return func(get_ge, **kwargs)
#    return wrapper

def target(target_func):
    def wrapper(get_ge=None, **kwargs):
        g,e,v = get_ge(ret_vac=True, **kwargs)
        
        in_states, out_states = target_func(g,e,v)

        in_states = [x.unit() for x in in_states]        
        out_states = [x.unit() for x in out_states]
        return in_states, out_states
    return wrapper


if 0: # Targets
    @target
    def make_cav_x_target(g,e,v):
        in_states = [g, e]
        out_states = [    g - 1j*e,
                      -1j*g +    e]
        return in_states, out_states
         
    @target
    def make_cav_y_target(g,e,v):
        in_states = [g, e]
        out_states = [g - e,
                      g +    e]
        return in_states, out_states
        
    @target
    def make_cav_m_target(g,e,v):
        in_states = [g, e]
        out_states = [    g + 1j*e,
                      1j*g +    e]
        return in_states, out_states

    @target
    def make_cav_n_target(g,e,v):
        in_states = [g, e]
        out_states = [g + e,
                      -1*g +    e]
        return in_states, out_states
        
    @target
    def make_cav_H_target(g,e,v):
        in_states =  [g, e]
        out_states = [ g+e,
                       g-e]        
        return in_states, out_states
    
    @target
    def make_cav_X_target(g,e,v):
        in_states =  [ g, e]
        out_states = [ e, g]        
        return in_states, out_states
        
    @target
    def make_cav_Y_target(g,e,v):
        in_states =  [ g, e]
        out_states = [ 1j*e, -1j*g]        
        return in_states, out_states

    @target
    def make_cav_Z_target(g,e,v):
        in_states =  [ g, e]
        out_states = [ g, -1*g]        
        return in_states, out_states
           
    @target             
    def make_cav_g_init_target(g,e,v):
        return [v,], [g,]
        
    @target
    def make_cav_e_init_target(g,e,v):
        return [v,], [e,]

    @target
    def make_cav_px_init_target(g,e,v):
        return [v,], [g+e,]

    @target
    def make_cav_py_init_target(g,e,v):
        return [v,], [g+1j*e,]

        
    # g, e represent the cavity
    def make_CNOT_cavControl_qbtTarget_target(get_ge=None, **kwargs): 
        g0,e0 = get_ge(qbt=0, **kwargs)
        g1,e1 = get_ge(qbt=1, **kwargs)

        in_states =  [g0, g1, e0, e1]
        out_states = [g0, g1, e1, e0]
        return in_states, out_states   
        
    def make_CNOT_qbtControl_cavTarget_target(get_ge=None,**kwargs): 
        g0,e0 = get_ge(qbt=0, **kwargs)
        g1,e1 = get_ge(qbt=1, **kwargs)
    
        in_states =  [g0, g1, e0, e1]
        out_states = [g0, e1, e0, g1]
        return in_states, out_states   

    def make_cav_qubit_cqMAP_target(get_ge=None,**kwargs): 
        g0,e0,v0 = get_ge(qbt=0, ret_vac=True, **kwargs)
        g1,e1,v1 = get_ge(qbt=1, ret_vac=True, **kwargs)
    
        in_states =  [g0, e0]
        out_states = [v0, v1]
        
        in_states  = [x.unit() for x in in_states]
        out_states = [x.unit() for x in out_states]
        return in_states, out_states

    def make_CNOT_tomo_target(get_ge=None,**kwargs): 
        g0,e0 = get_ge(qbt=0, **kwargs)
        g1,e1 = get_ge(qbt=1, **kwargs)
    
        in_states =  [g0, e0,]
        out_states = [g0, e1,]
        return in_states, out_states

    def make_CNOTthenHI_qbtControl_cavTarget_target(c_dim=23,**kwargs):  
        IH = tensor(qeye(c_dim), qutip.hadamard_transform())
        i, o = make_CNOT_qbtControl_cavTarget_target(c_dim=c_dim, **kwargs)
        
        return i, [IH * el for el in o]   

    def make_secret_plan_target(get_ge=None,c_dim=23,**kwargs):
        g,e = get_ge(c_dim=c_dim, **kwargs)
        a = qutip.tensor(qutip.destroy(c_dim), qutip.qeye(2))
        
        gp = (a * g).unit()
        ep = (a * e).unit()
        
        return [gp, ep], [g, e]  

    def make_cav_Xtomo_target(get_ge=None,**kwargs): 
        g0,e0 = get_ge(qbt=0, **kwargs)
        g1,e1 = get_ge(qbt=1, **kwargs)
    
        in_states =  [g0 + e0, g0 - e0]
        out_states = [g0 + e0, g1 - e1]
        
        in_states  = [x.unit() for x in in_states]
        out_states = [x.unit() for x in out_states]
        return in_states, out_states   

    def make_cav_Ytomo_target(get_ge=None,**kwargs): 
        g0,e0 = get_ge(qbt=0, **kwargs)
        g1,e1 = get_ge(qbt=1, **kwargs)
    
        in_states =  [g0 - 1j*e0, -1j*g0 +  e0]
        out_states = [g0, g1]
        
        in_states  = [x.unit() for x in in_states]
        out_states = [x.unit() for x in out_states]
        return in_states, out_states
        
def generate_gaussian(totlen, center, sigma=10):
    sigma = float(sigma)
    center = float(center)
    ts = np.arange(totlen)
    return np.exp(-(ts-center)**2/(2*sigma**2))
    
def generate_cosine_pulse(totlen):
    ts = np.arange(totlen)
    return np.sin(np.pi/totlen * ts)
    
def generate_echo(totlen, sigma=10, alpha=-210, t_offset=0, amp=None):
#    ts = np.arange(totlen)
    center1, center2 = totlen/4.0+t_offset, 3*totlen/4.0+t_offset
    
    if amp is None:
        amp = 100.0 / sigma #This gets the pi right for a 1 MHz drive
#    gauss1 = amp * np.exp(-(ts-center1)**2/(2*sigma**2))
#    gauss2 = amp * np.exp(-(ts-center0)**2/(2*sigma**2))
    gauss1 = amp * generate_gaussian(totlen, center1, sigma=sigma)
    gauss2 = amp * generate_gaussian(totlen, center2, sigma=sigma)
    I = gauss1 + gauss2
    
    
    return I, np.gradient(I) * 1.0/alpha
    

def grape_proc(plen=None, c_dim=9):

#    setup = [make_setup(c_dim=c_dim, q_dim=2, cav_exclusion=1),
#             make_setup(c_dim=c_dim+1, q_dim=2, cav_exclusion=1),
#             make_setup(c_dim=c_dim+2, q_dim=2, cav_exclusion=1)]
    setup = [make_setup(c_dim=c_dim, q_dim=2, cav_exclusion=1),]
             
    outdir = 'output\CT-op%s-len%s-cav%s' % (OPNAME, plen, c_dim, )

    init_ctrls = random_waves(len(names), plen)
      
    penalties = [
        make_amp_cost(1e-3, 500, iq_pairs=True),#200),#50), 
        make_deriv_cost(1e-4, 0.5),#1e-5, 0.5)
        make_l1_penalty(1e-6, 500)#1000)
    ]
      
    reporters = [
        save_waves(names, 20),
        plot_waves(names, 10),
        plot_fidelity(4),
    ]

    results = run_grape(init_ctrls, setup, penalties, reporters, 
                              outdir, maxiter=100, 
                              n_ss=1, dt=1, filt_func=FILT_FUNC,
                              n_proc=1, init_aux_params=aux_param)
    return {'outdir': results.outdir,
            'fid' : results.fids[0]}
        


def zmp_func(plen, c_dim, selector): 
    time.sleep(random.random()*5) # to avoid file interference
    q_dim = 2

    detunings1 = [0, 0, -113e-6, 0]

    if selector == 'GHZ':
        setup = [make_GHZ_setup(c_dim=c_dim, q_dim=q_dim),#, cav_exclusion=0, drive_mask=drive_mask),
                 make_GHZ_setup(c_dim=c_dim+1, q_dim=q_dim),#, cav_exclusion=0, drive_mask=drive_mask),
                 make_GHZ_setup(c_dim=c_dim+2, q_dim=q_dim),#, cav_exclusion=0, drive_mask=drive_mask),
                 make_GHZ_setup(c_dim=c_dim, q_dim=q_dim, detunings=detunings1),
                ]

        outdir = r'C:\Users\rsl\Desktop\stabilizer_grape'
        outdir += r'\output\GHZ-len%s-cav%s-qubit%s' % (plen, c_dim, q_dim, )


    elif selector == 'W':
        setup = [make_W_setup(c_dim=c_dim, q_dim=q_dim),#, cav_exclusion=0, drive_mask=drive_mask),
                 make_W_setup(c_dim=c_dim+1, q_dim=q_dim),#, cav_exclusion=0, drive_mask=drive_mask),
                 make_W_setup(c_dim=c_dim+2, q_dim=q_dim),#, cav_exclusion=0, drive_mask=drive_mask),
                 make_W_setup(c_dim=c_dim, q_dim=q_dim, detunings=detunings1),
                ]

        outdir = r'C:\Users\rsl\Desktop\stabilizer_grape'
        outdir += r'\output\W-len%s-cav%s-qubit%s' % (plen, c_dim, q_dim, )


    init_ctrls = random_waves(8, plen) * 1.0 
    
    reporters = [
        save_waves(names, 20),
        plot_waves(names, 10),
        plot_fidelity(4),

    ]
        
    results = run_grape(init_ctrls, setup, penalties, reporters, 
                              outdir, maxiter=1500, 
                              n_ss=1, dt=1, filt_func=FILT_FUNC,
                              n_proc=len(setup), init_aux_params=aux_param,
                              discrepancy_penalty=1e4)

    return {'outdir': results.outdir,
            'fid' : results.fids}
            
if 1 and __name__ == '__main__':


    A_A = -132.2e-3
    A_B = -123.2e-3
   
    H_A = (np.array([[0, X_A], [0, 0]]), [K_A, A_A,], [0, Xp_A,])
    H_B = (np.array([[0, X_B], [0, 0]]), [K_B, A_B,], [0, Xp_B,])


    zeta = -19e-6
    detunings = [0, zeta]
       
    names_A = get_IQ_id('cA') + get_IQ_id('qA')
    names_B = get_IQ_id('cB') + get_IQ_id('qB')
    
    # parameters for Yvonne
    X_Y = -838-6
    Xp_Y = 0
    K_Y = -4e-6
    A_Y = -182.504e-3
    H_Y = (np.array([[0, X_Y], [0, 0]]), [K_Y, A_Y,], [0, Xp_Y,])
    names_Y = get_IQ_id('cA') + get_IQ_id('qA')
    
    def do_A():
        return H_A, names_A
    def do_B():
        return H_B, names_B
    def do_Y():
        return H_Y, names_Y
                           
    default_penalties = [
        make_amp_cost(2e-3, 250, iq_pairs=False),#50), 
        make_deriv_cost(2e-5, 0.5),
        make_l1_penalty(1e-6, 500)#1e-5, 500
    ]

     

    if 1:  # Qubit Cal GRAPE (executes g-e pi pulse)
        plen = 200
        alpha = -0.195
        names = ['qAI', 'qAQ'] 

        setup = make_qubit_cal_setup(q_dim=2, alpha=alpha)
        outdir = 'output\qcal%s-len%s-qubitalpha%s' % (names[0][-2:],plen, int(-1e3*alpha) )
        
        init_ctrls = np.ones((len(names), plen))

        reporters = [
            print_costs(),
            save_waves(names, 20),
            plot_waves(names, 10),
            plot_fidelity(4),
            save_script(__file__),
        ]       
    
        results = run_grape(init_ctrls, setup, default_penalties, reporters, 
                            outdir, maxiter=500, 
                            n_ss=1, dt=2, filt_func=FILT_FUNC,
                            n_proc=1, init_aux_params=None)
        print results.outdir
                                  
             
    if 0:  # Cavity Cal GRAPE (executes displacement pulse)
        cavity_name = 'cA'
        
        plen = 48
        kerr = -1.25e-6 
        nbar = 1
        
        n_ss = 1 # simulation subsample
        dt = 2 # FPGA in 2 mode operation is 500 MHz        
        num_pts = plen / dt # number of points

        Ionly = False
        chop = 6.
        if Ionly:
            drive_mask = [1,0]
            dir_name = 'Ionly'
        else:
            drive_mask = [1,1]
            dir_name = 'IQ'
        
        setup = make_cav_cal_setup(c_dim=15, alpha=kerr, nbar=nbar, mask=drive_mask)
    
        names = get_IQ_id(cavity_name)
        outdir = 'output\%s-ccal-%s-len%s-kerr%s-nbar%f' % (dir_name, cavity_name, plen, int(-1e6*kerr), nbar )
        
        if Ionly:
            init_ctrls = [0.5*generate_gaussian(num_pts, num_pts/2.0, sigma=num_pts/chop),
                          np.zeros(num_pts),]
        else:
#            init_ctrls = np.ones((len(names), num_pts)) * 0.05
            init_ctrls = [0.35*generate_gaussian(num_pts, num_pts/2.0, sigma=num_pts/chop),]*len(names)

        reporters = [
            print_costs(),
            save_waves(names, 20),
            plot_waves(names, 10),
            plot_fidelity(4),
            save_script(__file__),
        ]     
        
        results = run_grape(init_ctrls, setup, default_penalties, reporters, 
                                  outdir, maxiter=500, 
                                  n_ss=n_ss, dt=dt, filt_func=FILT_FUNC,
                                  n_proc=1, init_aux_params=None)
        print results.outdir       
        print 'max wave amp: %.2f' % np.max(np.abs(results.controls))           


 