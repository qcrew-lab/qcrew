Introduction to GRAPE
=====================

Quantum Optimal Control
-----------------------

Gradient Ascent Pulse Engineering (GRAPE) is a technique for performing numerical quantum
optimal control. An optimal control problem is an optimization problem of the form

.. math::

    &\underset{\varepsilon(t)}{\text{minimize}}&\;& f[x(t)]\\
    &\text{subject to}&\;& \dot{x} = A(x(t), \varepsilon(t), t), \; x(0) = x_0

Where :math:`x` is the state of some system, :math:`\varepsilon` is some set of controls,
:math:`A` describes the system evolution, and :math:`f` is a cost functional, assigning values
to different trajectories, which we wish to minimize over all admissible functions
:math:`\varepsilon(t)`. In particular, the *quantum* optimal control problem has a few forms.

State Transfer
^^^^^^^^^^^^^^

.. math::

    x(t) &= |\psi(t)\rangle\\
    x(0) &= |\psi(0)\rangle\\
    A(x(t), \varepsilon(t), t) &= \frac{-i}{\hbar}(H_0 + \varepsilon(t) H_c)|\psi(t)\rangle\\
    f[x(t)] &= -\left|\langle \phi_\text{target} | \psi(T) \rangle\right|

Where :math:`H_0` is the base or drift hamiltonian, :math:`H_c` is the control Hamiltonian, and
:math:`|\psi(t)\rangle` is the state vector. We wish to then maximize the overlap between the
state vector and some target state :math:`|\phi_\text{target}\rangle` at some final time :math:`T`.

Unitary Evolution
^^^^^^^^^^^^^^^^^

.. math::

    x(t) &= U(t)\\
    x(0) &= \mathbb{I}\\
    A(x(t), \varepsilon(t), t) &= \frac{-i}{\hbar}(H_0 + \varepsilon(t) H_c)U(t)\\
    f[x(t)] &= -\left|\text{Tr}[U_\text{target}U^\dagger(T)]\right|

This is a generalization where we wish to optimize a full unitary transformation. This is equivalent
to optimizing N simultaneous orthogonal state transfers where N is the system dimension. Intermediate
problems taking the form of :math:`k < N` simultaneous state transfers are also possible.


Expectation Maximization
^^^^^^^^^^^^^^^^^^^^^^^^

This is the same as the state transfer problem, except for the cost functional

.. math::

    f[x(t)] &= -\langle \psi(T)| \hat{O} |\psi(T) \rangle

Where :math:`\hat{O}` is some observable operator.


Numerical Formulation
---------------------

Most optimal control problems do not have closed form solutions readily accessible. In order to find
solutions numerically, we must restrict our admissible functions to lie in some finite dimensional
space

.. math::

    \varepsilon(t) = \sum_{k=1}^N b_k g_k(t)

In GRAPE, we let the basis functions :math:`g_k(t)` be unit pulses in the interval
:math:`[k\delta t, (k+1)\delta t]` for some fixed :math:`\delta t`. I.e. we restrict ourselves to
piecewise constant functions with regular intervals. Our solutions then lie in a vector space of
dimension :math:`N = T / \delta t`. This restriction is suitable, since it presents an easy way
of calculating the total propagator, and also because at the end of the day we will be sending an
array of points to an AWG. With this parameterization, the propagator can be calculated as follows:

.. math::

    U(T) &= U_N U_{N-1} \ldots U_{2} U_1\\
    U_k &= \exp\left(-i (H_0 + b_k H_c) \delta t / \hbar\right)

Numerical Optimization
----------------------

Considering the unitary evolution formulation for a moment, we now have the problem

.. math::

    \underset{\mathbf{b}\in\mathbb{R}^N}{\text{minimize}} &\;& f(\mathbf{b})\\
    f(\mathbf{b}) &=& \left|\text{Tr}[U_\text{target}^\dagger U(b_N)\ldots U(b_1)]\right|

Since :math:`N` may be very large, the search space is of very high dimension. Moreover, the
calculation of :math:`f(\mathbf{b})` is computationally intensive, and may require a significant
amount of time. This problem can be circumvented if we can guide our search for a solution using
the *gradient*, :math:`\mathbf{g} = \nabla_\mathbf{b} f`. By calculating :math:`\mathbf{g}`,
we can try to take steps which always decrease the cost.

Calculating the Gradient
------------------------

.. math::

    \frac{\partial f}{\partial b_k} &= \left|\text{Tr}[U_\text{target}^\dagger U(b_N)
    \ldots \frac{\partial U(b_k)}{\partial b_k} \ldots U(b_1)]\right|\\
    \frac{\partial U(b_k)}{\partial b_k} &= \frac{\partial}{\partial b_k}e^{-\frac{i\delta t}{\hbar}(H_0 + b_k H_c)}\\

Calculating this derivative is somewhat involved. The derivation is presented for the sake
of completeness.

.. math::

    \frac{\partial}{\partial x} e^{A(x)} &=
    \frac{\partial}{\partial x} \lim_{N\rightarrow\infty} \left(\mathbb{I} + \frac{A}{N}\right)^N\\
    &= \lim_{N\rightarrow\infty} \sum_{k=1}^N \left(\mathbb{I} + \frac{A}{N}\right)^{k-1}
    \frac{\partial A}{\partial x} \left(\mathbb{I} + \frac{A}{N}\right)^{N-k}\\
    &= \int_0^1\!\!\mathrm{d}s\; e^{sA}\frac{\partial A}{\partial x}e^{(1-s)A}

If :math:`A` is an (anti-)hermitian operator, it has the eigendecomposition
:math:`A = V \Lambda V^\dagger` where :math:`V` is a unitary matrix whose columns are eigenvectors
and :math:`\Lambda` is a diagonal matrix whose elements are eigenvalues,
:math:`\Lambda_{ij} = \delta_{ij}\lambda_i`. Then, it follows that
:math:`e^{sA} = V e^{s\Lambda} V^\dagger`.

.. math::

    \frac{\partial}{\partial x} e^{A(x)} &=
    V \left(\int_0^1\!\!\mathrm{d}s\; e^{s\Lambda} V^\dagger
    \frac{\partial A}{\partial x}
    V e^{(1-s)\Lambda}\right)V^\dagger\\

Defining :math:`K \equiv V^\dagger \frac{\partial A}{\partial x} V`

.. math::

    \frac{\partial}{\partial x} e^{A(x)} &=
    V \left(\int_0^1\!\!\mathrm{d}s\; e^{s\Lambda} K e^{(1-s)\Lambda}\right)V^\dagger\\
    \left(\frac{\partial}{\partial x} e^{A(x)}\right)_{il}
    &= \sum_{jk}
    V_{ij} \left(\int_0^1\!\!\mathrm{d}s\; e^{s\lambda_j} K_{jk} e^{(1-s)\lambda_k}\right)V^\dagger_{kl}\\
    &= \sum_{jk}
    V_{ij} K_{jk} V^\dagger_{kl}
    \left(\int_0^1\!\!\mathrm{d}s\; e^{s\lambda_j} e^{(1-s)\lambda_k}\right)\\
    &= \sum_{jklm}
    V_{ij} K_{jk} V^\dagger_{kl}
    \frac{e^{\lambda_j} - e^{\lambda_k}}{\lambda_j - \lambda_k}\\

We define :math:`\Gamma_{jk} = \frac{e^{\lambda_j} - e^{\lambda_k}}{\lambda_j - \lambda_k}`. Note
that :math:`\lim_{\lambda_k \rightarrow \lambda_j} \Gamma_{jk} = e^{\lambda_j}`.

.. math::
    \left(\frac{\partial}{\partial x} e^{A(x)}\right)_{il}
    &= \sum_{jk}
    V_{ij} \Gamma_{jk} K_{jk} V^\dagger_{mn}\\
    \frac{\partial}{\partial x} e^{A(x)} &=
    V \left(\Gamma \odot K\right) V^\dagger\\
    &= V \left(\Gamma \odot \left(V^\dagger \frac{\partial A}{\partial x} V\right)\right) V^\dagger\\

Where :math:`\odot` is the hadamard product :math:`(A \odot B)_{ij} = A_{ij} B_{ij}`.

Then the derivative we originally sought is then

.. math::

    \frac{\partial U(b_k)}{\partial b_k}
    &= \frac{\partial}{\partial b_k}e^{-\frac{i\delta t}{\hbar}(H_0 + b_k H_c)}\\
    &= \frac{-i\delta t}{\hbar} V \left(\Gamma \odot \left(V^\dagger H_c V\right)\right) V^\dagger\\

Where :math:`V` and :math:`\Gamma` are from the eigendecomposition of :math:`H_0 + b_k H_c`

