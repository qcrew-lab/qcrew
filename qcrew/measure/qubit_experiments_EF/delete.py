#%%Simulation to obtain number-splitting
import matplotlib.pyplot as plt
import numpy as np
from qutip import *
from scipy.optimize import minimize
import h5py
import scipy as sc
import time
start_time = time.time()#checking how long the code takes

erf = sc.special.erf

qdim = 3
q = destroy(qdim)
qd = create(qdim)
ue = basis(qdim,1)
PPe = ue*ue.dag()#projector for excited state

#in GHz
chi = 1.359e-3
Kerr = 2*2.79e-6
alpha = 175.65e-3
cdim = 30

# TT2 = np.linspace(1,21,15)*1e3
TT2 = np.array([24.412, 23.652, 20.4, 16.496, 12.984, 9.892, 7.752, 5.9, 4.552, 3.5512, 3.0116, 2.1675, 1.1492, 0.7356, 0.462, 0.346, 0.2702, 0.21916, 0.1876, 0.16352, 0.14504, 0.12492, 0.11228, 0.10676, 0.0912])*1e3

pe = np.zeros(len(TT2))
for j in range(len(TT2)):
    T1 = 84e3#in ns
    T2 = TT2[j]#21e3#in ns
    Tphi = - 1/(1/2/T1 - 1/T2)
    cavT1 = 1.21e6#in ns
    cavT2 = 1.34e6#in ns
    nbar_cav = 0
    nbar_qb = 0.018#corresponds to pe=0.017
    rc0 = ket2dm(fock(cdim, nbar_cav))
    # prob = np.zeros(5)
    # for i in range(5):
    #     prob[i] = rc0[i,i].real

    # Contains information about the (pulse amplitude, pulse sigma, pulse chop)
    calibration = [
        (1, 250, 4),#tuple
    ]

    A, sigma, chop = calibration[0]

    matrix_elements = None
    peak_heights = None
    num_split_plot = None
    # c0 = np.array([
    #     177.406,
    #     176.05,
    #     174.69,
    #     173.325,
    #     171.92,
    #     170.535,
    #     169.135,
    #     167.7
    # ])
    freq_detune = 0;#np.linspace(171 -c0[0], 178.5 -c0[0], 101) * 1e-3# in GHz
    #this is wd-wq, -Delta. 

    if 1:
        '''
        Power Rabi: Use this to calibrate the amplitude needed to drive a qubit pi pulse
        '''
        amp = np.linspace(0, 1.5, 199)
        output = []

        for Ax in amp:
            A = np.sqrt(2/np.pi) / erf(np.sqrt(2))*np.pi/(4*sigma)/2/np.pi#initial guess
            A0 = A#keep it for later

            frq = 0#resonant driving

            A *= Ax#coefficient for the Gaussian pulse

            H0 = 2*np.pi*frq * qd*q - 2*np.pi*alpha/2*qd*qd*q*q
            Hd = 2*np.pi*A*1j*(qd - q)#or with other part Hd = 2*np.pi*A*(qd + q)

            def pulse(t, *arg):
                global sigma, chop
                t0 = sigma*chop/2

                g = np.exp( - 1/2 * (t - t0)**2 / sigma**2)

                return g

            H = [H0, [Hd, pulse]]

            #initial state
            # psi = basis(2, 0)
            rhoq = thermal_dm(qdim, nbar_qb)#ket2dm(psi)

            tlist = np.linspace(0, sigma*chop, 100)

            c_ops = [
                np.sqrt((1 + nbar_qb)/T1)*q,
                np.sqrt(nbar_qb/T1) * qd,
                np.sqrt(2/Tphi)*qd*q#changed
            ]

            e_ops = [PPe,]#[qd*q,]

            # options = Options(max_step = 1, nsteps = 1e6)

            results = mesolve(H, rhoq, tlist, c_ops= c_ops, e_ops = e_ops)#, options= options)#, progress_bar = True)

            output += [results.expect[0][-1],]
        
        # plt.plot(amp, output)
        # plt.ylabel(r"pe")
        # plt.xlabel("Amplitude Scale")
        # plt.title("Power Rabi")
        # plt.grid()
        # plt.show()

        # print(max(output), output.index(max(output)), amp[output.index(max(output))])
        A = A0*amp[output.index(max(output))]#this is the correct coeff
        
    if 1:
        '''
        Number Splitting simulation
        '''

        Q = tensor(destroy(qdim), qeye(cdim))
        C = tensor(qeye(qdim), destroy(cdim))

        Cd, Qd = C.dag(), Q.dag()

        frq = freq_detune
        H0 = -2*np.pi*frq * Qd*Q - 2*np.pi*chi*Qd*Q*Cd*C - 2*np.pi*Kerr/2*Cd*Cd*C*C - 2*np.pi*alpha/2*Qd*Qd*Q*Q
        Hd = 2*np.pi*1j*(Qd - Q)

        def pulse(t, *arg):
            t0 = sigma*chop/2
            g = A*np.exp( - 1/2 * (t - t0)**2 / sigma**2)

            return g

        H = [H0, [Hd, pulse]]

        # Initialise a thermal state
        psi = tensor(thermal_dm(qdim, nbar_qb), rc0)

        # Displace the state
        # psi = tensor(qeye(2),displace(cdim, 1),) * psi * tensor(qeye(2),displace(cdim, -1),)

        tlist = np.linspace(0, sigma*chop, 101)
        tlistw = np.linspace(0, 1280, 101)

        c_ops = [
        # Qubit Relaxation
        np.sqrt((1 + nbar_qb)/T1) * Q,
        # Qubit Thermal Excitations
        np.sqrt(nbar_qb/T1) * Qd,
        # Qubit Dephasing, changed
        np.sqrt(2/Tphi)*Qd*Q,
        # Cavity Relaxation
        np.sqrt((1 + nbar_cav)/cavT1) * C,
        # Cavity Thermal Excitations
        np.sqrt(nbar_cav/cavT1) * Cd,
        # Cavity Dephasing, changed
        np.sqrt(2/cavT2)*Cd*C,
        ]

        e_ops = [tensor(PPe,qeye(cdim)),]#[Qd*Q,]

        # options = Options(max_step = 4, nsteps = 1e6)
        results = mesolve(H, psi, tlist, c_ops= c_ops)#, e_ops = e_ops)#, options = options)#, progress_bar = True)
        #wait
        resultsw = mesolve(H0, results.states[-1], tlistw, c_ops= c_ops, e_ops = e_ops)#, options = options)#, progress_bar = True)
        pe[j] = resultsw.expect[0][-1]

plt.plot(TT2*1e-3,pe,'k-',label='pe_sim')
plt.xscale('log')
# plt.plot(TT2*1e-3,pe_approx,'or',label='pe_formula')
plt.legend()
plt.grid()
# plt.plot(TT,0.5*(1+np.exp(-k/2*TT)),'dg')
plt.ylim([0,1.05])
# plt.xticks(np.arange(min(TT2*1e-3), max(TT2*1e-3)+1, 2))
plt.xlabel('T2 [us]')
plt.show()
print(f"min pe is {np.min(pe)}")
print(f"max pe is {np.max(pe)}")

print("")
print("--- %s seconds ---" % (time.time() - start_time))
