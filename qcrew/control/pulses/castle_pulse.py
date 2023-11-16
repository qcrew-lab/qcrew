""" """

from time import thread_time
import numpy as np
from typing import ClassVar
from qcrew.control.pulses import integration_weights
from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class CastlePulse(Pulse):

    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "length_constant_1",
        "length_constant_2",
        "length_constant_3",
        "length_constant_4",
        "length_constant_5",
        "scale_amp_1",
        "scale_amp_2",
        "scale_amp_3",
        "scale_amp_4",
        "scale_amp_5",
    }

    def __init__(
        self,
        length_constant_1: int = 6,
        length_constant_2: int = 6,
        length_constant_3: int = 6,
        length_constant_4: int = 6,
        length_constant_5: int = 6,
        scale_amp_1: int = 1,
        scale_amp_2: int = 0.6,
        scale_amp_3: int = 0.8,
        scale_amp_4: int = -0.6,
        scale_amp_5: int = 0.1,
        ampx: float = None,
    ) -> None:
        """
        How about some explanations?
        I suppose that the length of the entire pulse is
        2 * length_ring + length_constant
        © Fernando
        """
        self.length_constant_1 = length_constant_1
        self.length_constant_2 = length_constant_2
        self.length_constant_3 = length_constant_3
        self.length_constant_4 = length_constant_4
        self.length_constant_5 = length_constant_5
        self.scale_amp_1 = scale_amp_1
        self.scale_amp_2 = scale_amp_2
        self.scale_amp_3 = scale_amp_3
        self.scale_amp_4 = scale_amp_4
        self.scale_amp_5 = scale_amp_5
        self.ampx = ampx
        length = (
            length_constant_1
            + length_constant_2
            + length_constant_3
            + length_constant_4
            + length_constant_5
        )
        super().__init__(length=length, ampx=ampx)

    def __call__(
        self,
        *,
        length_constant_1: int = None,
        length_constant_2: int = None,
        length_constant_3: int = None,
        length_constant_4: int = None,
        length_constant_5: int = None,
        scale_amp_1: int = None,
        scale_amp_2: int = None,
        scale_amp_3: int = None,
        scale_amp_4: int = None,
        scale_amp_5: int = None,
        ampx: float = None,
    ) -> None:
        """ """
        length = (
            length_constant_1
            + length_constant_2
            + length_constant_3
            + length_constant_4
            + length_constant_5
        )
        super().__call__(
            length_constant_1=length_constant_1,
            length_constant_2=length_constant_2,
            length_constant_3=length_constant_3,
            length_constant_4=length_constant_4,
            length_constant_5=length_constant_5,
            scale_amp_1=scale_amp_1,
            scale_amp_2=scale_amp_2,
            scale_amp_3=scale_amp_3,
            scale_amp_4=scale_amp_4,
            scale_amp_5=scale_amp_5,
            length=length,
            ampx=ampx,
        )

    @property
    def samples(self) -> tuple[np.ndarray]:
        constant_1 = np.full(
            self.length_constant_1, (BASE_PULSE_AMP * self.ampx * self.scale_amp_1)
        )
        constant_2 = np.full(
            self.length_constant_2, (BASE_PULSE_AMP * self.ampx * self.scale_amp_2)
        )
        constant_3 = np.full(
            self.length_constant_3, (BASE_PULSE_AMP * self.ampx * self.scale_amp_3)
        )
        constant_4 = np.full(
            self.length_constant_4, (BASE_PULSE_AMP * self.ampx * self.scale_amp_4)
        )
        constant_5 = np.full(
            self.length_constant_5, (BASE_PULSE_AMP * self.ampx * self.scale_amp_5)
        )
        i_wave = np.concatenate(
            (constant_1, constant_2, constant_3, constant_4, constant_5)
        )
        q_wave = np.zeros(
            self.length_constant_1
            + self.length_constant_2
            + self.length_constant_3
            + self.length_constant_4
            + self.length_constant_5
        )
        return i_wave, q_wave


# class ReadoutPulse(Pulse):
#     """ """

#     _parameters: ClassVar[set[str]] = Pulse._parameters | {
#         "pad",
#         "const_length_1",
#         "threshold",
#         "iw_path",
#     }

#     def __init__(
#         self,
#         *,
#         length: int = 400,
#         ampx: float = 1.0,
#         pad: int = 0,
#         const_length_1: int = 400,
#         const_length_2: int = 400,
#         const_length_3: int = 400,
#         const_length_4: int = 400,
#         const_length_5: int = 400,
#         scale_amp_1: int = None,
#         scale_amp_2: int = None,
#         scale_amp_3: int = None,
#         scale_amp_4: int = None,
#         scale_amp_5: int = None,
#         threshold: float = None,
#         integration_weights=None,
#     ) -> None:

#         self.pad = pad
#         self.const_length_1 = const_length_1
#         self.const_length_2 = const_length_2
#         self.const_length_3 = const_length_3
#         self.const_length_4 = const_length_4
#         self.const_length_5 = const_length_5
#         self.scale_amp_1 = scale_amp_1
#         self.scale_amp_2 = scale_amp_2
#         self.scale_amp_3 = scale_amp_3
#         self.scale_amp_4 = scale_amp_4
#         self.scale_amp_5 = scale_amp_5

#         length = (
#             pad
#             + const_length_1
#             + const_length_2
#             + const_length_3
#             + const_length_4
#             + const_length_5
#         )

#         self.threshold = threshold
#         # Saves the integration weights path as parameter if applicable
#         try:
#             self.iw_path = integration_weights.path
#         except AttributeError:
#             self.iw_path = None

#         super().__init__(
#             length=length, ampx=ampx, integration_weights=integration_weights
#         )

#     def __call__(
#         self,
#         *,
#         length: int = None,
#         pad: int = None,
#         const_length_1: int = None,
#         const_length_2: int = None,
#         const_length_3: int = None,
#         const_length_4: int = None,
#         const_length_5: int = None,
#         scale_amp_1: int = None,
#         scale_amp_2: int = None,
#         scale_amp_3: int = None,
#         scale_amp_4: int = None,
#         scale_amp_5: int = None,
#         ampx: float = None,
#         threshold: float = None,
#     ) -> None:
#         """ """
#         super().__call__(
#             length=length,
#             pad=pad,
#             const_length_1=const_length_1,
#             const_length_2=const_length_2,
#             const_length_3=const_length_3,
#             const_length_4=const_length_4,
#             const_length_5=const_length_5,
#             scale_amp_1=scale_amp_1,
#             scale_amp_2=scale_amp_2,
#             scale_amp_3=scale_amp_3,
#             scale_amp_4=scale_amp_4,
#             scale_amp_5=scale_amp_5,
#             ampx=ampx,
#             threshold=threshold,
#         )

#     @property
#     def samples(self) -> tuple[np.ndarray]:
#         constant_1 = np.full(
#             self.const_length_1, (BASE_PULSE_AMP * self.ampx * self.scale_amp_1)
#         )
#         constant_2 = np.full(
#             self.const_length_2, (BASE_PULSE_AMP * self.ampx * self.scale_amp_2)
#         )
#         constant_3 = np.full(
#             self.const_length_3, (BASE_PULSE_AMP * self.ampx * self.scale_amp_3)
#         )
#         constant_4 = np.full(
#             self.const_length_4, (BASE_PULSE_AMP * self.ampx * self.scale_amp_4)
#         )
#         constant_5 = np.full(
#             self.const_length_5, (BASE_PULSE_AMP * self.ampx * self.scale_amp_5)
#         )
#         i_wave = np.concatenate(
#             (constant_1, constant_2, constant_3, constant_4, constant_5)
#         )

#         q_wave = np.zeros(self.length)

#         if self.pad != 0:
#             pad_zeros = np.zeros(self.pad)
#             i_wave = np.concatenate((i_wave, pad_zeros), axis=0)

#         return i_wave, q_wave
