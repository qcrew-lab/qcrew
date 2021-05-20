""" """
from typing import ClassVar

from qcrew.helpers.pulsemaker import DEFAULT_CW_PULSE, DEFAULT_READOUT_PULSE, Pulse
from qcrew.instruments.meta.quantum_element import QuantumElement


class ReadoutResonator(QuantumElement):
    """ """

    # class variable defining the parameter set for ReadoutResonator objects
    _parameters: ClassVar[set[str]] = set(
        [
            "name",  # a unique name describing the ReadoutResonator
            "lo_freq",  # frequency of local oscillator driving the ReadoutResonator
            "lo_power",  # output power of local oscillator driving the ReadoutResonator
            "int_freq",  # intermediate frequency driving the ReadoutResonator
            "ports",  # input and output QuantumElementPorts of the ReadoutResonator
            "mixer",  # the IQMixer (if any) associated with the ReadoutResonator
            "ops",  # operations that can be performed on the ReadoutResonator
            "time_of_flight",  # as defined in the QM configuration specification
            "smearing",  # as defined in the QM configuration specification
        ]
    )

    # class variable defining the valid keysets of the ports of ReadoutResonator objects
    _ports_keysets: ClassVar[set[frozenset[str]]] = set(
        [
            frozenset(["inp", "out"]),
            frozenset(["I", "Q", "out"]),
        ]
    )

    # class variable defining the default operations dict for ReadoutResonator objects
    _default_operations: ClassVar[dict[str, Pulse]] = {
        "CW": DEFAULT_CW_PULSE,
        "readout": DEFAULT_READOUT_PULSE,
    }

    def __init__(
        self, time_of_flight: int = 180, smearing: int = 0, **parameters
    ) -> None:
        """ """
        self.time_of_flight: int = time_of_flight  # settable
        self.smearing: int = smearing  # settable
        super().__init__(**parameters)
