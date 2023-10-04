#%%
import numpy as np

def QN_regression(X_R, Y_R, lamb):
    Error = 0
    Ntr = len(X_R[0,:])
    RM = len(X_R[:,0])-1
    nD = len(Y_R[:,0])

    a1 = np.matmul(Y_R,np.transpose(X_R))
    b1 = np.linalg.inv(np.matmul(X_R,np.transpose(X_R))+lamb*np.eye(RM+1))
    beta = np.matmul(a1,b1)

    Er = np.zeros([Ntr, 1])
    for k in np.arange(0,Ntr):
        Y_id = Y_R[:,k] #targets
        X_ob = X_R[:,k] #1 and observables
        Y_est = np.matmul(beta,X_ob) #estimations
        Er[k] = np.sum(np.absolute(Y_id - Y_est))/nD
    Error = np.mean(Er)

    return Error, beta       