from system import *

"""
Ideal gates
ideal_operators no longer return the new state after the operator is applied.
"""


def D_ideal_operator(beta):
    return ((beta * a.dag() - np.conjugate(beta) * a)).expm()


def D_ideal(state: qt.Qobj, t_displace: list, epsilon) -> qt.Qobj:
    H_d = 1j * epsilon * a.dag() + np.conjugate(1j * epsilon) * a
    D = qt.mesolve(H_d, state, t_displace).states[-1]
    return D


def CD_ideal_operator(beta) -> qt.Qobj:
    # This Operator functions as specified in A. Eickbusch. beta = 1 creates two coherents states with |beta| = 0.5 with opposite sign.
    X = (a.dag() + a) / 2
    P = (1j * (a.dag() - a)) / 2
    CD = (1j * (np.real(beta) * P + np.imag(beta) * X) * sz).expm()
    return CD


def CD_ideal(state: qt.Qobj, t_displace: list, epsilon) -> qt.Qobj:
    X = (a.dag() + a) / 2
    P = (1j * (a.dag() - a)) / 2
    H_cd = (np.real(epsilon) * P + np.imag(epsilon) * X) * sz
    state = qt.mesolve(H_cd, state, t_displace).states[-1]
    return state


def U_ideal_operator(u_k):
    P = (1j * (a.dag() - a)) / 2
    Uk = (1j * u_k * P * sx).expm()
    return Uk


def V_ideal_operator(v_k):
    X = (a.dag() + a) / 2
    Vk = (1j * v_k * X * sy).expm()
    return Vk


# Gates implemented through Hamiltonian Evolution


def D(
    state: qt.Qobj, t_displace: list, epsilon, chi=CHI, phase_error=0, loss=None
) -> qt.Qobj:
    if loss is None:
        return qt.mesolve(
            H_dispersiveDrive(chi, epsilon * np.exp(1j * phase_error)),
            state,
            t_displace,
        ).states[-1]

    else:
        return qt.mesolve(
            H_dispersiveDrive(chi, epsilon * np.exp(1j * phase_error)),
            state,
            t_displace,
            c_ops=loss,
        ).states[-1]


# ECD like we do it currently in the experiment
def ECD_exp(
    state: qt.Qobj,
    t_displace: list,
    t_wait: list,
    alpha_scale,
    epsilon,
    chi=CHI,
    loss=None,
):
    if loss == None:
        # Execute ECD sequence as specifiedin in A.Eickbusch paper.
        psi1 = D(state, t_displace, alpha_scale * epsilon, chi)  # first displacement
        psi2 = qt.mesolve(H_dispersive(chi), psi1, t_wait).states[
            -1
        ]  # wait for time t_list[-1]
        psi3 = D(
            psi2, t_displace, -alpha_scale * epsilon * np.cos(chi * t_wait[-1] / 2), chi
        )  # first negative displacement
        psi4 = Rx(np.pi) * psi3
        psi5 = D(
            psi4, t_displace, -alpha_scale * epsilon * np.cos(chi * t_wait[-1] / 2), chi
        )
        psi6 = qt.mesolve(H_dispersive(chi), psi5, t_wait).states[-1]
        psi7 = D(
            psi6, t_displace, alpha_scale * epsilon * np.cos(chi * t_wait[-1]), chi
        )
        return psi7
    else:
        # Execute ECD sequence with loss
        rho1 = D(state, t_displace, alpha_scale * epsilon, chi, loss=loss)
        rho2 = qt.mesolve(H_dispersive(chi), rho1, t_wait, c_ops=loss).states[-1]
        rho3 = D(
            rho2,
            t_displace,
            -alpha_scale * epsilon * np.cos(chi * t_wait[-1] / 2),
            chi,
            loss=loss,
        )
        rho4 = Rx(np.pi) * rho3 * Rx(np.pi).dag()
        rho5 = D(
            rho4,
            t_displace,
            -alpha_scale * epsilon * np.cos(chi * t_wait[-1] / 2),
            chi,
            loss=loss,
        )
        rho6 = qt.mesolve(H_dispersive(chi), rho5, t_wait, c_ops=loss).states[-1]
        rho7 = D(
            rho6,
            t_displace,
            alpha_scale * epsilon * np.cos(chi * t_wait[-1]),
            chi,
            loss=loss,
        )
        return rho7


def ECD_exp_equal_displacements(
    state: qt.Qobj,
    t_displace: list,
    t_wait: list,
    alpha_scale,
    epsilon,
    chi=CHI,
    loss=None,
):
    if loss == None:
        # Execute ECD sequence as specifiedin in A.Eickbusch paper.
        psi1 = D(state, t_displace, alpha_scale * epsilon, chi)  # first displacement
        psi2 = qt.mesolve(H_dispersive(chi), psi1, t_wait).states[
            -1
        ]  # wait for time t_list[-1]
        psi3 = D(
            psi2, t_displace, -alpha_scale * epsilon, chi
        )  # first negative displacement
        psi4 = Rx(np.pi) * psi3
        psi5 = D(psi4, t_displace, -alpha_scale * epsilon, chi)
        psi6 = qt.mesolve(H_dispersive(chi), psi5, t_wait).states[-1]
        psi7 = D(psi6, t_displace, alpha_scale * epsilon, chi)
        return psi7

    else:
        # Execute ECD sequence with loss
        rho1 = D(state, t_displace, alpha_scale * epsilon, chi, loss=loss)
        rho2 = qt.mesolve(H_dispersive(chi), rho1, t_wait, c_ops=loss).states[-1]
        rho3 = D(
            rho2,
            t_displace,
            -alpha_scale * epsilon * np.cos(chi * t_wait[-1] / 2),
            chi,
            loss=loss,
        )
        rho4 = Rx(np.pi) * rho3 * Rx(np.pi).dag()
        rho5 = D(
            rho4,
            t_displace,
            -alpha_scale * epsilon * np.cos(chi * t_wait[-1] / 2),
            chi,
            loss=loss,
        )
        rho6 = qt.mesolve(H_dispersive(chi), rho5, t_wait, c_ops=loss).states[-1]
        rho7 = D(
            rho6,
            t_displace,
            alpha_scale * epsilon * np.cos(chi * t_wait[-1]),
            chi,
            loss=loss,
        )
        return rho7


def U(
    state: qt.Qobj,
    t_displace: list,
    t_wait: list,
    alpha_scale,
    epsilon,
    chi=CHI,
    phase_error=[0, 0, 0],
    loss=None,
):
    if loss is None:
        psi1 = Ry(-np.pi / 2 + phase_error[0]) * state
        psi2 = ECD_exp(psi1, t_displace, t_wait, -1j * alpha_scale, epsilon, chi, loss)
        psi3 = Rx(-np.pi + phase_error[1]) * psi2
        psi4 = Ry(np.pi / 2 + phase_error[2]) * psi3
        return psi4

    else:
        if state.type is "ket":
            state = qt.ket2dm(state)

        rho1 = (
            Ry(-np.pi / 2 + phase_error[0])
            * (state)
            * Ry(-np.pi / 2 + phase_error[0]).dag()
        )
        rho2 = ECD_exp(rho1, t_displace, t_wait, -1j * alpha_scale, epsilon, chi, loss)
        rho3 = Rx(-np.pi + phase_error[1]) * rho2 * Rx(-np.pi + phase_error[1]).dag()
        rho4 = (
            Ry(np.pi / 2 + phase_error[2]) * rho3 * Ry(np.pi / 2 + phase_error[2]).dag()
        )
        return rho4


def V(
    state: qt.Qobj,
    t_displace: list,
    t_wait: list,
    alpha_scale,
    epsilon,
    chi=CHI,
    phase_error=[0, 0, 0],
    loss=None,
):
    if loss is None:
        psi1 = Rx(np.pi / 2 + phase_error[0]) * state
        psi2 = ECD_exp(psi1, t_displace, t_wait, -alpha_scale, epsilon, chi, loss)
        psi3 = Rx(-np.pi + phase_error[1]) * psi2
        psi4 = Rx(-np.pi / 2 + phase_error[2]) * psi3
        return psi4

    else:
        if state.type is "ket":
            state = qt.ket2dm(state)
        rho1 = (
            Rx(np.pi / 2 + phase_error[0])
            * state
            * Rx(np.pi / 2 + phase_error[0]).dag()
        )
        rho2 = ECD_exp(rho1, t_displace, t_wait, -alpha_scale, epsilon, chi, loss)
        rho3 = Rx(-np.pi + phase_error[1]) * rho2 * Rx(-np.pi + phase_error[1]).dag()
        rho4 = (
            Rx(-np.pi / 2 + phase_error[2])
            * rho3
            * Rx(-np.pi / 2 + phase_error[2]).dag()
        )
    return rho4


def char_point(
    state,
    t_displace: list,
    t_wait: list,
    alpha_scale,
    epsilon,
    chi=CHI,
    loss=None,
    real=True,
):
    if loss is None:
        # bring qubit into superposition state
        psi1 = Ry(np.pi / 2) * state
        # apply ECD(beta), beta is a function of alpha and t_list[-1]

        psi2 = ECD_exp(psi1, t_displace, t_wait, -1j * alpha_scale, epsilon, chi)

        if real:
            psi3 = Ry(np.pi / 2) * psi2
        else:
            psi3 = Rx(np.pi / 2) * psi2

        return -(np.real(qt.expect(sz, psi3)))

    else:
        # bring qubit into superposition state
        rho1 = Ry(np.pi / 2) * qt.ket2dm(state) * Ry(np.pi / 2).dag()
        # apply ECD(beta), beta is a function of alpha and t_list[-1]
        rho2 = ECD_exp(rho1, t_displace, t_wait, -1j * alpha_scale, epsilon, chi, loss)
        if real:
            psi3 = Ry(np.pi / 2) * rho2 * Ry(np.pi / 2).dag()
        else:
            psi3 = Rx(np.pi / 2) * rho2 * Rx(np.pi / 2).dag()
        return -(np.real(qt.expect(sz, psi3)))
