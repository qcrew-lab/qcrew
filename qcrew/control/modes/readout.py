""" """

from typing import Callable, ClassVar

from qcrew.control.modes.mode import Mode
import qcrew.control.pulses as qcp
from qcrew.helpers import logger

from qm import qua


class Readout(Mode):
    """ """

    _parameters: ClassVar[set[str]] = Mode._parameters | {
        "omega",  # resonance frequency, in Hz
        "time_of_flight",
        "smearing",
    }
    _ports_keys: ClassVar[tuple[str]] = (*Mode._ports_keys, "out")
    _offsets_keys: ClassVar[tuple[str]] = (*Mode._offsets_keys, "out")

    _demod_method_map: ClassVar[dict[str, Callable]] = {
        "sliced": qua.demod.sliced,
        "accumulated": qua.demod.accumulated,
        "window": qua.demod.moving_window,
    }

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        omega: float = None,
        time_of_flight: int = 180,
        smearing: int = 0,
        **parameters,
    ) -> None:
        """ """
        super().__init__(**parameters)

        if "readout_pulse" not in self._operations:
            integration_weights = qcp.ConstantIntegrationWeights()
            readout_pulse = qcp.ConstantPulse(integration_weights=integration_weights)
            self.operations = {"readout_pulse": readout_pulse}

        self.omega: float = omega
        self.time_of_flight: int = time_of_flight
        self.smearing: int = smearing

    def measure(
        self,
        targets: tuple,
        stream: str = None,
        demod_type: str = "full",
        demod_args: tuple = None,
    ) -> None:
        """ """
        iw_key_i, iw_key_q = self.readout_pulse.integration_weights.keys
        var_i, var_q = targets

        if demod_type == "full":
            output_i, output_q = (iw_key_i, var_i), (iw_key_q, var_q)
            demod_i, demod_q = qua.demod.full(*output_i), qua.demod.full(*output_q)
            qua.measure("readout_pulse", self.name, stream, demod_i, demod_q)
        else:
            try:
                demod_method = self._demod_method_map[demod_type]
            except KeyError:
                logger.error(f"Unrecognized demod type '{demod_type}'")
                raise
            else:
                output_i = (iw_key_i, var_i, *demod_args)
                output_q = (iw_key_q, var_q, *demod_args)
                demod_i, demod_q = demod_method(*output_i), demod_method(*output_q)
                qua.measure("readout_pulse", self.name, stream, demod_i, demod_q)
