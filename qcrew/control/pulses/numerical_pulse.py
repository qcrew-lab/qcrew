""" """

from pathlib import Path

import numpy as np

from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class NumericalPulse(Pulse):
    """ """

    def __init__(self, path: str, ampx: float = 1.0, pad: int = 0) -> None:
        """
        To initialise the Numerical Pulse class

        Parameters
        -----------
        path : str
            To point to the ".npz" save file of the numerical pulse
        ampx : float
            amplitude of the pulse
        pad : int
            padding of the pulse

        return
        -----------
        NumericalPulse obj
        """
        self.path = path
        self.pad = pad

        npzfile = np.load(Path(self.path))
        self.oct_pulse_X = npzfile["pulseX"]
        self.oct_pulse_Y = npzfile["pulseY"]

        # Checking if the quadratures have the same pulse length
        quad_len_diff = len(self.oct_pulse_X) - len(self.oct_pulse_Y)
        if quad_len_diff != 0:
            print("Pulse Quadrature Lengths are Different: Padding Tail ... ")

            if quad_len_diff < 0:
                self.oct_pulse_X = np.append(
                    npzfile["pulseX"], [0] * (quad_len_diff * -1)
                )
            elif quad_len_diff > 0:
                self.oct_pulse_Y = np.append(npzfile["pulseY"], [0] * quad_len_diff)

        length = len(self.oct_pulse_X)

        if length % 4 != 0:
            self.pad = 4 - length % 4
            length += self.pad

        super().__init__(length=length, ampx=ampx, integration_weights=None)

    @property
    def samples(self):
        """ """
        ########## REDACTED ##########

        # i_wave = np.real(self.oct_pulse) * BASE_PULSE_AMP * self.ampx
        # q_wave = np.imag(self.oct_pulse) * BASE_PULSE_AMP * self.ampx

        ########## REDACTED ##########

        i_wave = self.oct_pulse_X * BASE_PULSE_AMP * self.ampx
        q_wave = self.oct_pulse_Y * BASE_PULSE_AMP * self.ampx

        print(np.max(np.real(self.oct_pulse_X)))
        print(np.max(np.imag(self.oct_pulse_Y)))
        print(np.max(i_wave))
        print(np.max(q_wave))

        if self.pad != 0:
            pad_zeros = np.zeros(self.pad)
            i_wave = np.concatenate((i_wave, pad_zeros), axis=0)
            q_wave = np.concatenate((q_wave, pad_zeros), axis=0)

        return i_wave, q_wave
