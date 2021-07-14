""" """

from qcrew.control.pulses.pulse import Pulse
from qcrew.control.pulses.constant_pulse import ConstantPulse
from qcrew.control.instruments.vaunix.labbrick import LabBrick
from typing import ClassVar
from qcrew.control.modes.mode import Mode


class Readout(Mode):
    """ """

    _parameters: ClassVar[set[str]] = Mode._parameters | {"time_of_flight", "smearing"}
    _ports_keys: ClassVar[tuple[str]] = (*Mode._ports_keys, "out")
    _offsets_keys: ClassVar[tuple[str]] = (*Mode._offsets_keys, "out")

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        time_of_flight: int = 180,
        smearing: int = 0,
        **parameters,
    ) -> None:
        """ """
        super().__init__(**parameters)

        self.time_of_flight: int = time_of_flight
        self.smearing: int = smearing

        if "readout_pulse" not in self._operations:
            self.operations = {  # NOTE integration weight is hard-coded for now
                "readout_pulse": ConstantPulse(integration_weights=ConstantPulse()),
            }
