from scipy import optimize
import time
import numpy as np
import matplotlib.pyplot as plt
from qutip import destroy, Qobj, rand_dm, displace, expect, fock, fock_dm
from QN_regression import QN_regression

start_time = time.time()  # checking how long the code takes

# the optimization
D = 6  # Dimension to read
n_dis = D**2 - 1
RM = n_dis  # no of readouts, at least D^2-1
nD = n_dis  # no of parameters for general states
Ntr = D**2  # no of training for obtaining the map, at least D^2

# cdim = 10

# print(expect(fock_dm(cdim,5), displace(cdim,  0.23174872 + 1.11633499j)* fock(cdim, 1)))


if D == 6:
    # AL = set of alphas

    AL = np.array(
        [
            -0.48187911 - 0.41734485j,
            0.23174872 + 1.11633499j,
            0.0504064 + 0.37541931j,
            1.25255274 + 2.10872826j,
            -0.49435492 + 0.85599798j,
            -0.43038545 + 0.41356184j,
            0.5271912 - 0.90156403j,
            1.34540633 - 0.04074134j,
            -0.36563645 + 0.07605901j,
            1.3414531 - 0.85587375j,
            1.1784257 - 1.86134276j,
            0.3304149 - 1.83180835j,
            0.56397487 + 1.92516705j,
            -0.92046236 - 0.53307494j,
            1.61672018 - 1.18572345j,
            -1.93318253 + 0.13849422j,
            0.85784998 + 0.45969804j,
            -0.04803121 - 0.36488883j,
            -0.30659985 - 1.03377411j,
            -1.1081292 - 0.72326863j,
            1.92364126 + 1.10348993j,
            1.8786748 + 0.19507815j,
            1.04505317 - 0.25137013j,
            -1.03336391 + 1.86140358j,
            -0.14376649 + 1.45048125j,
            0.36290604 - 0.01712708j,
            0.70374509 + 1.31715702j,
            -1.3956255 + 0.94748531j,
            -1.076281 + 0.4800951j,
            -1.43333961 + 0.01043554j,
            -0.35077402 - 1.28910182j,
            0.66220139 - 1.09556791j,
            0.28725183 - 0.52748209j,
            -1.84746916 - 1.32407537j,
            0.47432052 + 0.36741188j,
        ]
    )

    # AL = np.array([ # old
    #         -0.85703772 - 0.41103671j,
    #         0.73225389 - 0.96982265j,
    #         -0.21834647 + 0.34849838j,
    #         -1.58388171 + 0.10675561j,
    #         -0.22752489 - 0.98946425j,
    #         0.30810916 + 1.35605743j,
    #         0.38449679 - 0.01448902j,
    #         -0.44457373 - 1.27659996j,
    #         -0.65445865 + 1.14111546j,
    #         0.68337999 + 0.54264186j,
    #         1.65072948 - 0.58656416j,
    #         1.15339348 - 1.04776075j,
    #         -1.46868592 - 0.83841492j,
    #         -1.40366236 + 0.85371123j,
    #         -1.47560326 - 1.42267674j,
    #         -0.23425394 - 0.59579021j,
    #         -0.04762233 - 0.37541208j,
    #         -0.07400758 + 0.77805875j,
    #         -0.14728009 - 2.30294012j,
    #         -0.6559489 - 1.55382849j,
    #         0.99241771 - 0.10471466j,
    #         -1.02881791 + 0.54348621j,
    #         1.23896643 + 0.09430688j,
    #         -0.59414584 + 0.23776207j,
    #         1.72710934 + 0.58854817j,
    #         -1.04325339 - 0.61871112j,
    #         -1.54134671 + 1.48896059j,
    #         0.81723316 - 1.89940617j,
    #         0.51779053 - 0.8204179j,
    #         -2.01598037 - 0.10784227j,
    #         -1.51330818 - 1.98816387j,
    #         -0.59696256 + 1.67346801j,
    #         0.58965213 - 0.08301175j,
    #         0.54737316 - 1.62678537j,
    #         0.85286478 + 0.93814954j,
    #     ]
    # )

    # number_dis * peaks per dis = d2-1
    # TM = n_dis  # no of time multiplexing instances
    TM1 = 0
    TM2 = 0
    TM3 = 0
    TM4 = 0
    TM5 = 35  # 35 points measured p5


# elif D==5:
#     # D5
#     AL = np.array([-1.1848571 +0.8096053j , -1.00933408-0.345056j  ,
#     -1.52223563-0.04413064j,  0.75142788-0.23834468j,
#     1.4343226 +0.78057228j,  0.62963919+0.40864702j,
#     -0.27088106-1.04416493j,  0.51992756+0.30268825j,
#     -0.12314268+1.327761j  ,  1.49149501-0.11959137j,
#     -0.48826335+0.48197647j, -0.59888712-1.37432475j,
#     -1.13485624+1.14524419j, -0.90709117-0.35785598j,
#     0.11325643+0.94850705j,  1.03258476+0.91627408j,
#     -0.32048601+1.7938981j , -0.31784596+0.26316093j,
#     -0.35660681-0.55927563j,  0.61724267+1.65008629j,
#     0.59088513-1.02627816j,  0.28546229+0.28482724j,
#     0.33134764-0.73575301j,  0.26215286-0.25804249j])
#     TM = n_dis #no of time multiplexing instances
#     TM1 = 0; TM2 = 1; TM3 = 5; TM4 = 18; TM5 = 0
# elif D==4:
#     # D4
#     AL = np.array([ 0.38225617-0.99489863j,
#     -1.11579993-0.00203959j,
#     0.61395454+0.72252121j,
#     1.03740582+0.96512163j,
#     0.81294727-0.01561215j,
#     0.09494793+0.88061383j,
#     -0.35772628+1.17679072j,
#      0.49695525+0.16147493j,
#     -0.32299587+0.44293726j,
#     -0.72274272+0.51109849j,
#     -0.16474317-0.56787676j,
#     -0.97859858-0.45892448j,
#     -0.42746846-1.05407622j,
#     0.51310245-0.8432099j ,
#     1.2550222 -0.17791612j])
#     TM = n_dis #no of time multiplexing instances
#     TM1 = 0; TM2 = 4; TM3 = 11; TM4 = 0; TM5 = 0
# elif D==3:
#     #D3
#     #V1
#     # AL = np.array([ 0.57863806-0.93198782j,
#     # 1.16819202+0.20517804j,
#     # -0.68051864-0.97162374j,
#     # -0.59790946-0.09166605j,
#     # 0.350262  +0.5254438j ,
#     # 0.30295808-0.51612308j,
#     # 0.94265909-0.40006609j,
#     # -0.11101738-1.03555541j])
#     # TM = n_dis #no of time multiplexing instances
#     # TM1 = 3; TM2 = 5; TM3 = 0; TM4 = 0; TM5 = 0
#     #V2
#     # AL = np.array([-0.95040539+0.42519812j, -0.90905749-0.67886449j,
#     # 0.27366296-1.11402019j, -0.39735878-0.35625519j,
#     # 0.41298282-0.37997875j, -0.80163061-0.31612061j,
#     # 0.44362567-0.80529768j,  0.21684883+0.65408395j])
#     # TM = n_dis #no of time multiplexing instances
#     # TM1 = 3; TM2 = 5; TM3 = 0; TM4 = 0; TM5 = 0
#     #V3
#     # AL = np.array([ 0.51630871-1.22405262j, -0.82581514+0.88918515j,
#     # 0.41611041+1.40065629j, -0.77553896-0.38058551j,
#     # -0.53695919-0.04815008j,  0.0656359 +0.52181275j,
#     # 0.63208816-0.30365848j,  1.20010965+0.60014593j])
#     # TM = n_dis #no of time multiplexing instances
#     # TM1 = 2; TM2 = 6; TM3 = 0; TM4 = 0; TM5 = 0
#     #V4
#     AL = np.array([-0.38983945-1.14467135j, -1.16158054+0.28790215j,
#     -0.79299043-0.54624414j,  0.5678252 -0.19872388j,
#     0.25991564-1.12786646j, -0.81957003+0.72830491j,
#     0.03548759+0.60160004j, -0.5008095 -0.3371377j ])
#     TM = n_dis #no of time multiplexing instances
#     TM1 = 2; TM2 = 6; TM3 = 0; TM4 = 0; TM5 = 0
# elif D==2:
#     #D2
#     AL = np.array([-0.21655953+0.36502677j,  0.42437394+0.00505914j,
#     -0.20783834-0.36999038j])
#     TM = n_dis #no of time multiplexing instances
#     TM1 = 3; TM2 = 0; TM3 = 0; TM4 = 0; TM5 = 0


cdim = 30  # truncation
a = destroy(cdim)  # annihilation for cavity


# displacement operator
def Dis(alpha):
    U = (alpha * a.dag() - np.conj(alpha) * a).expm()
    return U


# this part if for obtaining the map X=MY+V, where X are the observables (peaks) and Y are the elements of rho
X_r = np.zeros([1 + RM, Ntr])  # store readouts 36x35
X_r[0, :] = np.ones([1, Ntr])  # setting the ones in first row of X
Y_rnd = np.zeros([nD, Ntr])  # store the targets 35x36

for j in np.arange(0, Ntr):
    # Assign targets
    rho_rnd = np.zeros([cdim, cdim], dtype=np.complex_)
    rho_rnd[0:D, 0:D] = rand_dm(D)  # random density matrix
    Y_rnd[0 : D - 1, j] = np.diagonal(rho_rnd).real[0 : D - 1]  # Diagonal of rho
    off_diag = rho_rnd[np.triu_indices(D, 1)]  # Upper triangle of rho
    Y_rnd[D - 1 :: 2, j] = np.real(off_diag)
    Y_rnd[D::2, j] = np.imag(off_diag)
    r0 = Qobj(rho_rnd)

    w = 0
    for v in np.arange(0, TM1):
        # T = float(T)#because the optimize gives T an np.array type
        U = Dis(AL[w])
        rt = U * r0 * U.dag()
        X_r[w + 1, j] = rt[1, 1].real  # + 0*np.random.normal(0, xi, 1)
        w += 1
    for v1 in np.arange(0, TM2):
        # T = float(T)#because the optimize gives T an np.array type
        U = Dis(AL[w])
        rt = U * r0 * U.dag()
        X_r[w + 1, j] = rt[2, 2].real  # + 0*np.random.normal(0, xi, 1)
        w += 1
    for v2 in np.arange(0, TM3):
        # T = float(T)#because the optimize gives T an np.array type
        U = Dis(AL[w])
        rt = U * r0 * U.dag()
        X_r[w + 1, j] = rt[3, 3].real  # + 0*np.random.normal(0, xi, 1)
        w += 1
    for v3 in np.arange(0, TM4):
        # T = float(T)#because the optimize gives T an np.array type
        U = Dis(AL[w])
        rt = U * r0 * U.dag()
        X_r[w + 1, j] = rt[4, 4].real  # + 0*np.random.normal(0, xi, 1)
        w += 1
    for v4 in np.arange(0, TM5):
        U = Dis(AL[w])
        rt = U * r0 * U.dag()
        X_r[w + 1, j] = rt[5, 5].real  # + 0*np.random.normal(0, xi, 1)
        w += 1

# ridge regression
lamb = 0

# training, now to obtain the map
X_R = np.zeros([1 + nD, Ntr])  # will contain the parameters
X_R[0, :] = np.ones([1, Ntr])  # setting the ones
Y_R = np.zeros([RM, Ntr])  # will contain the obs

# re-defining variables
X_R[1 : nD + 1, :] = Y_rnd  # X_R are the elements of rho
Y_R[:, :] = X_r[1 : RM + 1, :]  # Y_R are the observables

Error, beta = QN_regression(X_R, Y_R, lamb)  # beta has M and V s.t. X=MY+V

M = beta[:, 1 : nD + 1]  # the map
W = np.matmul(np.linalg.inv(np.matmul(np.transpose(M), M)), np.transpose(M))
eta = np.linalg.norm(M, 2) * np.linalg.norm(W, 2)
print("CD = ", eta)
print("")
print("--- %s seconds ---" % (time.time() - start_time))
