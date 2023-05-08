""" """
""" """

from qcrew.control.pulses.pulse import Pulse

class DigitalMarkerPulse(Pulse):
    """ """

    DEFAULT_SAMPLES: list[tuple[int, int]] = [(1, 0)]

    def __init__(
        self, name: str, length: int = 400, ampx: float = 1.0, samples: list[tuple[int, int]] = None, **parameters
    ) -> None:
        """ """
        # Overwrites the value in Pulse parent class.
        self.has_mix_waveforms = False
        # [(value, length)] where value = 0 (LOW) or 1 (HIGH) and length is in ns
        # length = 0 means value will be played for remaining duration of the waveform
        self.name = name
        self.samples = DigitalMarkerPulse.DEFAULT_SAMPLES if samples is None else samples
        #super().__init__(name=name, **parameters)
        super().__init__(length=length, ampx=ampx)