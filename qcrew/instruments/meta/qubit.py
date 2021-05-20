""" """
from typing import ClassVar

from qcrew.helpers.pulsemaker import DEFAULT_CW_PULSE, DEFAULT_GAUSSIAN_PULSE, Pulse
from qcrew.instruments.meta.quantum_element import QuantumElement


class Qubit(QuantumElement):
    """ """

    # class variable defining the parameter set for Qubit objects
    _parameters: ClassVar[set[str]] = set(
        [
            "name",  # a unique name describing the Qubit
            "lo_freq",  # frequency of local oscillator driving the Qubit
            "lo_power",  # output power of local oscillator driving the Qubit
            "int_freq",  # intermediate frequency driving the Qubit
            "ports",  # input QuantumElementPorts of the Qubit
            "mixer",  # the IQMixer (if any) associated with the Qubit
            "ops",  # operations that can be performed on the Qubit
        ]
    )

    # class variable defining the valid keysets of the ports of Qubit objects
    _ports_keysets: ClassVar[set[frozenset[str]]] = set(
        [
            frozenset(["inp"]),
            frozenset(["I", "Q"]),
        ]
    )

    # class variable defining the default operations dict for Qubit objects
    _default_ops: ClassVar[dict[str, Pulse]] = {
        "CW": DEFAULT_CW_PULSE,
        "gaussian": DEFAULT_GAUSSIAN_PULSE,
    }
