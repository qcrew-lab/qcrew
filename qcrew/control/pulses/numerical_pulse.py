""" """

from pathlib import Path

import numpy as np

from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class NumericalPulse(Pulse):
    """ """

    def __init__(self, path: str, I_quad : str, Q_quad : str, ampx: float = 1.0, pad: int = 0, frontpad: int = 0) -> None:
        """
        To initialise the Numerical Pulse class

        Parameters
        -----------
        path : str
            To point to the ".npz" save file of the numerical pulse

        I_quad : str
            The dictionary hash of the I_quadrature of the pulse
        
        Q_quad : str
            The dictionary hash of the Q_quadrature

        ampx : float
            amplitude scaling of the pulse; limited to ±2

        pad : int
            rear padding of the pulse with zeros; to ensure the quadratures have the same length

        front_pad : int
            Front padding of the pulse with zeros; used for alignment of multiple pulses to account for TOF of lines

        return
        -----------
        NumericalPulse obj
        """

        self.path = path
        self.pad = pad
        self.frontpad = frontpad
        
        npzfile = np.load(Path(self.path), "r")

        self.oct_pulse_X = npzfile[I_quad]     # First Quadrature
        self.oct_pulse_Y = npzfile[Q_quad]     # second Quadrature

        self.time_step = npzfile["dt"]         # Time Step between Specified Pulse Amplitudes

        # Checking if the specified time step is valid (in ns)
        if int(self.time_step) != self.time_step:
            raise Exception("The time step should be an integer (in ns)")
        self.time_step = int(self.time_step)

        # For pulses with time step > 1, we make sure the pulse is extrapolated to the right length
        self.oct_pulse_X = np.repeat(self.oct_pulse_X, self.time_step)
        self.oct_pulse_Y = np.repeat(self.oct_pulse_Y, self.time_step)

        # Adding the time delay to the pulse
        self.oct_pulse_X = np.append(
            [0,]*self.frontpad, self.oct_pulse_X)
        self.oct_pulse_Y = np.append(
            [0,]*self.frontpad, self.oct_pulse_Y)

        # Checking if the quadratures have the same pulse length
        quad_len_diff = len(self.oct_pulse_X) - len(self.oct_pulse_Y)

        if quad_len_diff != 0:
            print("Pulse Quadrature Lengths are Different: Padding Tail ... ")

            if quad_len_diff < 0:
                self.oct_pulse_X = np.append(
                    self.oct_pulse_X, [0] * (quad_len_diff * -1)
                )
            elif quad_len_diff > 0:
                self.oct_pulse_Y = np.append(
                    self.oct_pulse_Y, [0] * quad_len_diff
                )

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
