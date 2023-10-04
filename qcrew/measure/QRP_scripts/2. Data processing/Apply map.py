import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import h5py
from qutip import *
from QN_regression import QN_regression
from qnqn import tr1_rho, PSD_rho
import h5py

D = 6
nD = D**2 - 1

dir = r"C:\Users\qcrew\Desktop\QRP data\QRP_29092023_D6"

falseData = True
postSel = True

states_directory = r"C:\Users\qcrew\Desktop\qcrew\qcrew\config\GRAPE\GRAPE states n=0"  

#GRAPE dir
qdim = 3  # GRAPE qubit dim
cdim = 30  # GRAPE cavity dim

state_list = []
point_list = []

for file in Path(dir).glob("*"):
    file_name = file.stem[::]
    state_name = "".join(file_name.split("D=6_")[1].split("_point")[0])
    if state_name not in state_list:
        state_list.append(state_name)
    point = file_name.split("_point")[1]
    if point not in point_list:
        point_list.append(point)

state_list.remove("coh1")
# state_list = ["vacuum"]

print("Using", len(state_list), "states, with", len(point_list), "points each.")

print("States:", state_list)

print("Is the data unreliable?:", falseData)

print("Post-selection?:", falseData)

arr = []
# Post-selection function
def select(filepath, postSel):
    file = h5py.File(filepath, "r")
    data = file["data"]
    threshold = file["operations/readout_pulse"].attrs["threshold"]
    I = data["I"][::]
    x = data["x"][::]  # Assume all sweep points are the same
    sweep_points = int(np.shape(x)[0])  # 5
    flat_data = I.flatten()
    I_first = flat_data[0::2]
    I_second = flat_data[1::2]
    num_of_reps = int(np.shape(I_first)[0] / sweep_points)
    I_first = np.reshape(I_first, (num_of_reps, sweep_points))
    I_second = np.reshape(I_second, (num_of_reps, sweep_points))

    # Transform into 0s and 1s
    I_first = [[int(cell) for cell in row] for row in (I_first > threshold)]
    I_second = [[int(cell) for cell in row] for row in (I_second > threshold)]
    
    
    I_first = np.transpose(I_first)
    I_second = np.transpose(I_second)
    
    I_AVG_first = []
    I_AVG_second = []

    for sweep_point, row in enumerate(I_first):  # Select I_fist only 0s
        indices = np.array(row).nonzero()
        print("Throwing away", len(indices[0]), "runs out of", len(row),":",
              len(indices[0])/len(row)*100 ,"%")
        
        arr.append(len(indices[0])/len(row))
        
        if postSel:
            avg_first = np.average(np.delete(I_first[sweep_point], indices))
            avg_second = np.average(np.delete(I_second[sweep_point], indices))
        else:
            avg_first = np.average(I_first[sweep_point])
            avg_second = np.average(I_second[sweep_point])

        I_AVG_first.append(avg_first)
        I_AVG_second.append(avg_second)
    return I_AVG_second


# select(r'C:\Users\admin\Desktop\QRP\DATA\2meas_PND_D=6_vacuum_point1.h5')
# Target state function simulating GRAPE pulses and ideal displacements
def Y_target(state_name, qRho_est, states_directory):
    # Target states
    if state_name == "vacuum":
        rho_tar = fock_dm(cdim, 0)  # Assume cavity in perfect vacuum
    else:
        file = np.load(states_directory + "/" + state_name[6:] + ".npz", "r")
        # 6 is to remove "pulse_"
        rho_tar = Qobj(file["rho"], dims=[[qdim, cdim], [qdim, cdim]]).ptrace(1)

    rho_tar_D = Qobj(rho_tar[0:D, 0:D])  # no need 30 DIMS, CUT AT 6
    rho_tar_D = rho_tar_D / rho_tar_D.tr()  # normalise it, .unit()
    # Target observables
    Y_tar = np.zeros(nD)
    Y_tar[: D - 1] = np.diagonal(rho_tar_D).real[:-1]  # Diagonal of rho
    off_diag = rho_tar_D[np.triu_indices(6, 1)]  # Upper triangle of rho
    Y_tar[D - 1 :: 2] = np.real(off_diag)
    Y_tar[D::2] = np.imag(off_diag)
    Fi = fidelity(rho_tar_D, qRho_est) ** 2
    return Y_tar, Fi


# Builds a density matrix from the vector Y
def rho_from_Y(Y_est):
    rho_est = np.zeros([D, D], dtype=np.complex_)
    diagonal = np.append(Y_est[: D - 1], 1 - sum(Y_est[: D - 1]))
    np.fill_diagonal(rho_est, diagonal)  # Populate diagonal of rho

    index_i_list = np.triu_indices(D, 1)[0]
    index_j_list = np.triu_indices(D, 1)[1]
    for k in range(len(index_i_list)):  # Populate off-diagonals of rho
        index_i = index_i_list[k]
        index_j = index_j_list[k]
        rho_est[index_i, index_j] = Y_est[D - 1 + 2 * k] + 1j * Y_est[D + 2 * k]
        rho_est[index_j, index_i] = Y_est[D - 1 + 2 * k] - 1j * Y_est[D + 2 * k]

    return Qobj(rho_est)


def target_state(name):
    if len(name) == 5:  # fock0, fock1, fock2...
        target = fock(cdim, int(name[-1]))
        return target

    elif len(name) == 6:  # fock01, fock02, fock34...
        target = (fock(cdim, int(name[-2])) + fock(cdim, int(name[-1]))).unit()
        return target

    elif len(name) == 7:  # fock0i1, fock0i2, fock3i4...
        target = (fock(cdim, int(name[-3])) + 1j * fock(cdim, int(name[-1]))).unit()
        return target

    else:
        print("State ", name, "invalid!")
        pass


F = np.zeros(len(state_list), dtype=float)
err = np.zeros(len(state_list), dtype=float)
Obs_exp = np.zeros([len(point_list), len(state_list)])
all_files = np.array(os.listdir(dir))  # May be redundant with Path(dir) above

# Mapping
C = np.matmul(-W, beta[:, 0])
BETA = np.zeros([nD, RM + 1])
BETA[:, 0] = C
BETA[:, 1 : RM + 1] = W

# Peak frequencies, NOT USED NOW
# c0 = np.array([-60.00, -61.35, -62.72, -64.08, -65.47, -66.86])

for j, state_name in enumerate(state_list):  # State List
    data = np.zeros([len(point_list)])  # Initialize data vector

    if state_name == 'vacuum':
        ideal = fock(cdim, 0)
    else:
        ideal = target_state(state_name[6:])

    for point in range(1, len(point_list) + 1):  # Point1 to Point35
        ending = (
            "D=" + str(D) + "_" + str(state_name) + "_point" + str(point) + ".h5"
        )  # extract D=6 another way
        matching = [
            filename for filename in all_files if filename.endswith(str(ending))
        ]
        filepath = dir + "/" + matching[0]
        file = h5py.File(filepath, "r")
        
        if falseData:
            # data[point - 1] = np.average(select(filepath))  # No scaling
            aux = (np.average(select(filepath, postSel)) - 0.5) / 0.936 + 0.5  
            # scaling
            data[point - 1] = aux

        else:
            print("WIP")
            continue
            # data[point - 1] = (file["data"]["state"][0] - 0.5) / 0.936 + 0.5
            # data[point - 1] = (np.mean(file["data"]["state"]) - 0.035) / (0.944-0.035)
            # data = (data - 0.5) / 0.936 + 0.5  # factor 1 if preselection
            
        theory = expect(fock_dm(cdim, 5), displace(cdim, AL[point-1]) * ideal)
        # print("Theory says:", theory)
        # print("We get:", aux)
        # print("")

    # Experimental observables
    X_exp = np.zeros([1 + len(data)])
    X_exp[0] = 1
    X_exp[1:] = data

    # print("from exp data", X_exp)
    # Estimate the state by applying the inverse map to the experimental data
    Y_est = np.zeros(nD)
    Y_est = np.matmul(BETA, X_exp)
    rho_est = rho_from_Y(Y_est)  # just a reshaping
    qRho_est = PSD_rho(rho_est)  # make it positive semi-definite, Lagrange multipliers

    # X_tar = np.zeros([1 + len(data)])
    # X_tar[0] = 1
    # for p, point in enumerate(AL):
    #     state_disp = displace(cdim, point) * fock(cdim, 0)
    #     X_tar[p + 1] = expect(fock_dm(cdim, 5), state_disp)
    # print(X_tar)

    # Figures of merit
    Y_tar, F[j] = Y_target(state_name, qRho_est, states_directory)
    diff = Y_tar - Y_est
    err[j] = np.sqrt((np.dot(diff, diff)) / len(Y_tar))
    Obs_exp[:, j] = data  # THIS FOR WHAT

print("Fidelity:", F)
print(f"Average fidelity is {np.mean(F)}")
print(f"Average error is {np.mean(err)}")

# Fid: it's in another script, considers GRAPE + all simulation of pulses with coherent error, so it's worse than Y_t

np.average(arr)