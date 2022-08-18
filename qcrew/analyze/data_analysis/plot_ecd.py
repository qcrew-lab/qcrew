import h5py
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma

if 1:
    filepath = "C:/Users/qcrew/Desktop/qcrew/data/panther_transmon/20220817/221448_panther_ECD_char_postselect.h5"
    file = h5py.File(filepath, "r")
    data = file["data"]
    data_i = data["I"][:]
    # state = data["state"][:]
    x = data["x"][:, 0][:, 0]
    n_points = len(x)  # sweep points
    thresh = -9.847929226626616e-06
    ss_data = np.where(data_i < thresh, 1, 0)
    m1 = ss_data[:, 0::2]  # .mean(axis=0) # first measurement, we use as mask
    m2 = ss_data[:, 1::2]  # .mean(axis=0) # second measurement
    # mask = np.zeros_like(m1)
    mx_g = ma.masked_array(m2, mask=m1).mean(axis=0).reshape(n_points, n_points) * 2 -1
    mx_e = (
        ma.masked_array(m2, mask=np.logical_not(m1))
        .mean(axis=0)
        .reshape(n_points, n_points)
    ) * 2 -1
    mx_ge = m2.mean(axis=0).reshape(n_points, n_points) * 2 - 1

    # test = m1.mean(axis=0).reshape(31, 31) 
    fig, ax = plt.subplots()
    proj_ge = [mx_g, mx_e, mx_ge]  # m2.mean(axis = 0).reshape(n_points, n_points)
    index_1 = 2
    f = ax.pcolormesh(x, x, proj_ge[index_1], cmap="bwr")
    # ax.set_title("%i" % index_1)
    if index_1 == 0:
        ax.set_title("proj_ge: mx_g")
    elif index_1 == 1:
        ax.set_title("proj_ge: mx_e")
    else:
        ax.set_title("proj_ge: mx_ge")
    ax.set_aspect("equal")
    ax.set_xlabel(r"real($\beta$)")
    ax.set_ylabel(r"imag($\beta$)")
    fig.colorbar(f)


if 0:
    filepath = "C:/Users/qcrew/Desktop/qcrew/data/panther_transmon/20220812/103308_panther_power_rabi.h5"
    file = h5py.File(filepath, "r")
    data = file["data"]
    x = np.array(data["x"][:, 0])
    data_i = data["I"][:]
    thresh = -9.847929226626616e-06
    ss_data = np.where(data_i < thresh, 1, 0)

    m1 = ss_data[:, 0::2]  # .mean(axis=0)
    m2 = ss_data[:, 1::2]  # .mean(axis=0)

    mx_g = ma.masked_array(m2, mask=m1).mean(axis=0)
    mx_e = ma.masked_array(m2, mask=np.logical_not(m1)).mean(axis=0)

    plt.plot(x, mx_g, "r*")
    plt.plot(x, mx_e, "b")

    # I_AVG = data["I_AVG"]
    # fig, ax = plt.subplots()
    # # ax.pcolormesh(x_vec, y_vec, I_AVG, cmap = 'bwr', shading='auto' )
    # ax.plot(x_vec, I_AVG[:,19])
    # ax.set_title('measured')
    # ax.set_aspect("equal")
