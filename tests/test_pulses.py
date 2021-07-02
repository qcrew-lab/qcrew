""" Test script for adding and updating pulses"""
from tests.test_modes import qubit, rr
from pprint import pp

pp(rr.operations)

pp(rr.readout_pulse)

qubit.constant_pulse(length=10, ampx=0.4)

qubit.gaussian_pulse(ampx=1, sigma=)


