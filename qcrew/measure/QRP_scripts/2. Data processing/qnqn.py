#%% 
import numpy as np
from qutip import Qobj,qeye

def PSD_rho(rho):#-> pos semi definite rho, given hermitian with trace 1
    d = rho.shape[0]
    w,v = np.linalg.eig(rho)
    idx = np.argsort(w)[::-1]#reverse, now from largest to smallest
    w = w[idx]
    v = v[:,idx]

    la = 0*w#to store eigenvalues of new state
    a = 0#accumulator
    i = d-1#index

    while w[i]+a/(i+1)<0:
        la[i] = 0
        a += w[i]
        i += -1
    
    for k in np.arange(0,i+1):
        la[k] = w[k]+a/(i+1)
    
    rho_f = 0*rho.full()#store final density matrix
    for x in np.arange(0,len(la)):
        rho_f = rho_f+(la[x]*Qobj(v[:,x])*Qobj(v[:,x]).dag()).full()
    
    return Qobj(rho_f)

def tr1_rho(M,W):
    d = int(np.sqrt(M.shape[1]))
    Id = qeye(d)
    Idvec = (np.transpose(Id)).reshape((d**2,1))#identity in vec form
    MM = np.zeros([d**2+1,d**2+1], dtype=complex)
    XX = np.zeros([d**2+1,1], dtype=complex)
    MM[:d**2,:d**2] = M.dag()*M
    MM[:d**2,d**2] = np.transpose(Idvec)#apparently it works like this
    MM[d**2,:d**2] = np.transpose(Idvec)
    MM[d**2,d**2] = 0
    XX[:d**2,0] = np.transpose(M.dag()*W)#apparently it works like this
    XX[d**2,0] = 1
    YY = np.matmul(np.linalg.inv(MM),XX)
    rvec_est = YY[:d**2,0]
    return rvec_est