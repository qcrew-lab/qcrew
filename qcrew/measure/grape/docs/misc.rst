.. py:currentmodule::pygrape
.. default-role:: any

Advice & FAQ
============

Choosing an initial pulse
-------------------------

The choice of initial pulse is an important but subtle factor in the performance of the algorithm.
An incorrect choice could cause the algorithm to fail to converge, or return an unacceptable answer.
For instance:

- a choice of all zeros will often fail because this is often a local minimum in the
  fidelity, where the derivative is zero.
- similarly, a choice with symmetries which can be broken in multiple ways by desired solution
  will fail for the same reason.
- a choice which is random at every point will usually converge to a solution, but the solution is
  usually unacceptable, since it will also appear "noisy", i.e. have high frequency components.

A suitable solution is then a smoothed random initial pulse. `random_waves` is a convenience function
for this purpose. It smoothly interpolates between a set of random points. You should choose the
smallest number of points necessary to break all of the symmetries you expect.

Choosing a pulse length
-----------------------

Unfortunately, there is no prescription to offer here. If the pulse length is too short,
the fidelity will never exceed some maximum value smaller than unity. One must experiment to find
out which lengths work and which don't. The relationship is not necessarily monotonic either, in
that shorter pulses can sometimes converge much faster than longer pulses. A reasonable choice is
to identify some critical frequency in the Hamiltonian, and take some number of periods.

Linear Harmonic Oscillators
---------------------------

When optimizing pulses for linear harmonic oscillators, one runs into the issue of truncation.
In a real system, driving with a constant amplitude will never return you to the vacuum, but
in a truncated system, there always exists some driving amplitude for which you will "wrap around".

.. raw:: html

    <video src="_static/truncation.mp4" style="margin: auto; display: block;" controls></video>

To avoid this unphysical behavior, it often suffices to perform the optimization in two spaces
with differing truncations.::

    def make_setup(trunc):
        a = qutip.destroy(trunc)
        ...
        return H0, Hcs, U_target

    setups = [make_setup(15), make_setup(16)]

The truncation dependence can be gauged by evaluating the performance in a system
with a larger truncation.::


    reprorters = [
        ...
        verify_from_setup(make_setup(17)
    ]
    run_grape(..., reporter_fns=reporters)

If a discrepancy persists while using multiple truncations, it might be necessary to move
to a nonhermitian hamiltonian.

.. literalinclude:: ../examples/a_cubed_drive.py


Monitoring the Optimization Progress
------------------------------------

Many times the optimization will take a good deal of time to complete. To reduce the cost of
mistakes, it is better to catch them early. The mechanism for observing the progress of the
optimization is using :ref:`reporters`, which are instances of the :ref:`Reporter` class
supplied to the ``reporters`` argument of the `run_grape` function. After every step of the
algorithm, each of the supplied reporters is called using the data generated during that step.
The data supplied to the reporter is indicated by the names of its arguments. The supported names
are listed in the `run_grape` documentation. For instance, to print the total cost after each
5 iterations::

    class print_total_cost(Reporter):
        def run(tot_cost):
            print tot_cost

    run_grape(..., reporter_fns=[print_total_cost(5)])

This works because ``tot_cost`` is a supported name corresponding to the total cost.

Parallel Execution
------------------

If multiple setups are used, each setup can be run in parallel on a separate process.
To enable this feature, set the ``n_proc`` argument to `run_grape` to a value larger
than 1.

