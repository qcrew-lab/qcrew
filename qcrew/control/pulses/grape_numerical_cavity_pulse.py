""" """

from pathlib import Path

import numpy as np

from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class GrapeNumericalCavityPulse(Pulse):
    """ """

    def __init__(self, path: str, ampx: float = 1.0, pad: int = 0, frontpad: int = 0) -> None:
        """
        To initialise the GRAPE Numerical Pulse class

        Parameters
        -----------
        path : str
            To point to the ".npz" save file of the numerical pulse
        ampx : float
            amplitude of the pulse
        pad : int
            rear padding of the pulse with zeros
        front_pad : int
            Front padding of the pulse with zeros

        return
        -----------
        NumericalPulse obj
        """

        self.path = path
        self.pad = pad
        self.frontpad = frontpad

        npzfile = np.load(Path(self.path), "r")

        self.oct_pulse_X = npzfile["CavityI"]     # First Quadrature
        self.oct_pulse_Y = npzfile["CavityQ"]     # second Quadrature

        self.time_step = npzfile["dt"]            # Time Step between Specified Pulse Amplitudes

        # Checking if the specified time step is valid (in ns)
        if int(self.time_step) != self.time_step:
            raise Exception("The time step should be an integer in ns")
        self.time_step = int(self.time_step)

        # For pulses with time step > 1, we make sure the pulse is extrapolated to the right length
        self.oct_pulse_X = np.repeat(npzfile["CavityI"], self.time_step)
        self.oct_pulse_Y = np.repeat(npzfile["CavityQ"], self.time_step)

        # Checking if the quadratures have the same pulse length
        quad_len_diff = len(self.oct_pulse_X) - len(self.oct_pulse_Y)

        if quad_len_diff != 0:
            print("Pulse Quadrature Lengths are Different: Padding Tail ... ")

            if quad_len_diff < 0:
                self.oct_pulse_X = np.append(
                    npzfile["CavityI"], [0] * (quad_len_diff * -1)
                )
            elif quad_len_diff > 0:
                self.oct_pulse_Y = np.append(npzfile["CavityQ"], [0] * quad_len_diff)

        length = len(self.oct_pulse_X)

        # Check if the pulse is a multiple of four, because QM works that way
        if length % 4 != 0:
            self.pad = 4 - length % 4
            length += self.pad

        super().__init__(length=length, ampx=ampx, integration_weights=None)

    @property
    def samples(self):
        """ """

        i_wave = self.oct_pulse_X * self.ampx
        q_wave = self.oct_pulse_Y * self.ampx

        if self.pad != 0:
            pad_zeros = np.zeros(self.pad)
            i_wave = np.concatenate((i_wave, pad_zeros), axis=0)
            q_wave = np.concatenate((q_wave, pad_zeros), axis=0)

        return i_wave, q_wave
