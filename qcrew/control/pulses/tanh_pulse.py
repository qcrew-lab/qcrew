""" """

from time import thread_time
import numpy as np
from typing import ClassVar
from qcrew.control.pulses import integration_weights
from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class TanhPulse(Pulse):

    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "length_ring",
        "length_constant",
    }

    def __init__(
        self, length_ring: int, length_constant: int, ampx: float = None
    ) -> None:
        """ """
        self.length_ring = length_ring
        self.length_constant = length_constant
        self.ampx = ampx
        length = 2 * length_ring + length_constant
        super().__init__(length=length, ampx=ampx)

    def __call__(
        self,
        *,
        length_ring: int = None,
        length_constant: int = None,
        ampx: float = None
    ) -> None:
        """ """
        length = 2 * length_ring + length_constant
        super().__call__(
            length_ring=length_ring,
            length_constant=length_constant,
            length=length,
            ampx=ampx,
        )

    @property
    def samples(self) -> tuple[np.ndarray]:
        # ring_up = self.ring_up_wave(self.length_ring)
        ring_down = self.ring_up_wave(self.length_ring, reverse=True)
        # constant = np.full(self.length_constant, (BASE_PULSE_AMP * self.ampx))
        i_wave = np.concatenate((ring_down))

        # i_wave = np.concatenate((ring_up, constant, ring_down))

        q_wave = np.zeros(self.length_ring)

        # q_wave = np.zeros(self.length_constant + 2 * self.length_ring)
        return i_wave, q_wave

    def ring_up_wave(self, length_ring, reverse=False, shape="cos"):
        if shape == "cos":
            i_wave = self.ring_up_cos(length_ring)
        elif shape == "tanh":
            i_wave = self.ring_up_tanh(length_ring)
        else:
            raise ValueError("Type must be 'cos' or 'tanh', not %s" % shape)
        if reverse:
            i_wave = i_wave[::-1]
        return i_wave

    def ring_up_cos(self, length_ring):
        return (
            0.5
            * (1 - np.cos(np.linspace(0, np.pi, length_ring)))
            * (BASE_PULSE_AMP * self.ampx)
        )

    # def ring_up_tanh(self, length_ring):
    #     ts = np.linspace(-2, 2, length_ring)
    #     return (1 + np.tanh(ts)) / 2 * (BASE_PULSE_AMP * self.ampx)
