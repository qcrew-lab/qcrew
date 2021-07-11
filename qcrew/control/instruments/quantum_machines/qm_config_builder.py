""" """

from collections import defaultdict
from typing import Any, Union

import numpy as np
from qcrew.control.modes.mode import Mode
from qcrew.control.pulses.pulses import Pulse, ConstantPulse
from qcrew.helpers import logger

from qcrew.control.instruments.quantum_machines import (
    AI_MAX,
    AI_MIN,
    AO_MAX,
    AO_MIN,
    CLOCK_CYCLE,
    CONTROLLER_NAME,
    CONTROLLER_TYPE,
    BASE_AMP,
    MCM_MAX,
    MCM_MIN,
    MIN_PULSE_LEN,
    RO_DIGITAL_MARKER,
    RO_DIGITAL_SAMPLES,
    V_MAX,
    V_MIN,
)


class InfinitelyNestableDict(defaultdict):
    """ """

    def __init__(self) -> None:
        """ """
        super().__init__(InfinitelyNestableDict)

    def __repr__(self) -> str:
        """ """
        return repr(dict(self))


class QMConfig(InfinitelyNestableDict):
    """ """

    setters: dict[str, str] = {
        "lo_freq": "set_lo_freq",
        "int_freq": "set_int_freq",
        "ports": "set_ports",
        "offsets": "set_offsets",
        "opspec": "set_operations",
        "time_of_flight": "set_time_of_flight",
        "smearing": "set_smearing",
    }

    def set_version(self) -> None:
        """ """
        self["version"] = 1

    def set_controllers(self) -> None:
        """ """
        self["controllers"][CONTROLLER_NAME]["type"] = CONTROLLER_TYPE

    def get_mixer_name(self, mode_name: str) -> str:
        """ """
        return mode_name + ".mixer"

    def set_mixers(self, *modes: Mode) -> None:
        """ """
        mixer_config_keys = {"intermediate_frequency", "lo_frequency", "correction"}
        for mode in modes:
            try:
                if mode.has_mix_inputs:
                    mixer_name = self.get_mixer_name(mode.name)
                    mixer_config_schema = {key: None for key in mixer_config_keys}
                    self["mixers"][mixer_name] = [mixer_config_schema]
                    self["elements"][mode.name]["mixInputs"]["mixer"] = mixer_name
                    logger.success(f"Set '{mixer_name}' for {mode}")
            except AttributeError as e:
                logger.exception(f"Failed to determine if {mode} has mix inputs")
                raise SystemExit("Failed to set mixers in QM config, exiting...") from e

    def set_lo_freq(self, mode: Mode, old_value: dict[str, Any] = None) -> None:
        """ """
        try:
            lo_freq = int(mode.lo_freq)
        except AttributeError as e:
            logger.exception(f"Failed to get {mode} lo frequency")
            raise SystemExit("Failed to set lo freq in QM config, exiting...") from e
        else:
            self["elements"][mode.name]["mixInputs"]["lo_frequency"] = lo_freq
            self["mixers"][self.get_mixer_name(mode.name)][0]["lo_frequency"] = lo_freq
            old_value = None if old_value is None else old_value["frequency"]
            logger.success(f"Set {mode} lo freq from {old_value} to {lo_freq}")

    def set_int_freq(self, mode: Mode, old_value: float = None) -> None:
        """ """
        try:
            int_freq = int(mode.int_freq)
        except (TypeError, ValueError) as e:
            logger.exception(f"Invalid {mode} int_freq value, expect ({int},{float})")
            raise SystemExit("Failed to set int freq in QM config, exiting...") from e
        else:
            self["elements"][mode.name]["intermediate_frequency"] = int_freq
            mixer_name = self.get_mixer_name(mode.name)
            self["mixers"][mixer_name][0]["intermediate_frequency"] = int_freq
            logger.success(f"Set {mode} int freq from {old_value} to {int_freq}")

    def set_ports(self, mode: Mode, old_ports: dict[str, int] = None) -> None:
        """ """
        new_ports = mode.ports

        if old_ports is not None and set(new_ports) != set(old_ports):
            logger.error("Forbidden to change mode ports keyset")
            raise ValueError(f"Forbidden: {old_ports} -> {new_ports}")

        old_ports = old_ports if old_ports is not None else dict()
        diff_ports = dict(set(new_ports.items()) - set(old_ports.items()))
        for key, port_num in diff_ports.items():
            try:
                self.set_controller_port(mode, key, port_num)
            except TypeError:
                logger.exception(f"Expect port number of {int}, got {port_num}")
                raise
            else:
                self.set_element_port(mode, key, port_num)

    def set_controller_port(self, mode: Mode, key: str, port_num: int) -> None:
        """ """
        controllers_config = self["controllers"][CONTROLLER_NAME]
        offset = mode.offsets[key]
        if key in ("I", "Q"):
            if not AO_MIN <= port_num <= AO_MAX:
                logger.error(f"AO port value {port_num} out of bounds")
                raise ValueError(f"Out of bounds [{AO_MIN}, {AO_MAX}]")
            controllers_config["analog_outputs"][port_num]["offset"] = offset
            logger.success(f"Set {mode} AO port {port_num} with {offset = }")
        elif key == "out":
            if not AI_MIN <= port_num <= AI_MAX:
                logger.error(f"AI port value {port_num} out of bounds")
                raise ValueError(f"Out of bounds [{AI_MIN}, {AI_MAX}]")
            controllers_config["analog_inputs"][port_num]["offset"] = offset
            logger.success(f"Set {mode} AI port {port_num} with {offset = }")

    def set_element_port(self, mode: Mode, key: str, port_num: int) -> None:
        """ """
        mode_config = self["elements"][mode.name]
        if key in ("I", "Q") and mode.has_mix_inputs:
            mode_config["mixInputs"][key] = (CONTROLLER_NAME, port_num)
        elif key == "out":
            key = key + str(port_num)
            mode_config["outputs"][key] = (CONTROLLER_NAME, port_num)
        elif key == "I" and not mode.has_mix_inputs:
            mode_config["singleInput"]["port"] = (CONTROLLER_NAME, port_num)

    def set_offsets(self, mode: Mode, old_offsets: dict[str, float] = None) -> None:
        """ """
        mixer_name = self.get_mixer_name(mode.name)
        offsets = mode.offsets
        if old_offsets is None:  # on first pass, set_controller_port() sets DC offsets
            self.set_mixer_correction_matrix(mixer_name, (offsets["G"], offsets["P"]))
        else:
            diff_offsets = dict(set(offsets.items()) - set(old_offsets.items()))
            if any((key in diff_offsets.keys() for key in ("G", "P"))):
                g_offset, p_offset = diff_offsets.pop("G"), diff_offsets.pop("P")
                self.set_mixer_correction_matrix(mixer_name, (g_offset, p_offset))
            for key, offset in diff_offsets.items():
                self.set_dc_offset(mode, key, offset)

    @classmethod
    def get_mixer_correction_matrix(cls, g: float, p: float) -> tuple[float]:
        """ """
        try:
            cos = np.cos(p)
            sin = np.sin(p)
            coeff = 1 / ((1 - g ** 2) * (2 * cos ** 2 - 1))
        except TypeError as e:
            logger.exception(f"Invalid offset value(s), expect {float}")
            raise SystemExit("Failed to set offsets in QM config, exiting...") from e
        else:
            array = ((1 - g) * cos, (1 + g) * sin, (1 - g) * sin, (1 + g) * cos)
            return tuple(float(coeff * x) for x in array)

    def set_mixer_correction_matrix(self, mixer: str, offsets: tuple[float]) -> None:
        """ """
        correction_matrix = self.get_mixer_correction_matrix(*offsets)

        for value in correction_matrix:
            if not MCM_MIN < value < MCM_MAX:
                logger.error(f"Mixer correction matrix {value = } out of bounds")
                raise ValueError(f"Out of bounds ({MCM_MIN}, {MCM_MAX})")

        self["mixers"][mixer][0]["correction"] = correction_matrix
        logger.success(f"Set '{mixer}' correction matrix to {correction_matrix}")

    def set_dc_offset(self, mode: Mode, key: str, offset: float) -> None:
        """ """
        try:
            if not V_MIN < offset < V_MAX:
                logger.error(f"DC {offset = } out of bounds")
                raise ValueError(f"Out of bounds ({V_MIN}, {V_MAX})")
        except TypeError as e:
            logger.exception(f"Invalid offset value(s), expect {float}")
            raise SystemExit("Failed to set offsets in QM config, exiting...") from e

        controller_config = self["controllers"][CONTROLLER_NAME]
        ports = mode.ports
        if key == "out":
            controller_config["analog_inputs"][ports[key]]["offset"] = offset
            logger.success(f"Set {mode} AI DC {offset = }")
        elif key in ("I", "Q"):
            controller_config["analog_outputs"][ports[key]]["offset"] = offset
            logger.success(f"Set {mode} AO DC '{key}' {offset = }")

    def set_time_of_flight(self, mode: Mode, old_value: int = None) -> None:
        """ """
        try:
            tof = int(mode.time_of_flight)
        except (TypeError, ValueError) as e:
            logger.exception(f"Invalid {mode} time of flight value, expect {int}")
            raise SystemExit("Failed to set tof in QM config, exiting...") from e
        else:
            if tof % CLOCK_CYCLE != 0:
                tof = CLOCK_CYCLE * round(tof / CLOCK_CYCLE)
                logger.warning(f"Rounded tof to nearest multiple of {CLOCK_CYCLE}")
            self["elements"][mode.name]["time_of_flight"] = tof
            logger.success(f"Set {mode} time of flight from {old_value} to {tof}")

    def set_smearing(self, mode: Mode, old_value: int = None) -> None:
        """ """
        try:
            smearing = int(mode.smearing)
        except (TypeError, ValueError) as e:
            logger.exception(f"Invalid {mode} smearing value, expect {int}")
            raise SystemExit("Failed to set smearing in QM config, exiting...") from e
        else:
            self["elements"][mode.name]["smearing"] = smearing
            logger.success(f"Set {mode} smearing from {old_value} to {smearing}")

    def set_operations(self, mode: Mode, old_ops: dict[str, Any] = None) -> None:
        """ """
        ops = mode.opspec

        ops_config = self["elements"][mode.name]["operations"]
        for op_name, op_parameters in ops.items():
            pulse = getattr(mode, op_name)
            pulse_name = self.get_pulse_name(mode.name, op_name)
            if old_ops is None or op_name not in old_ops:  # new op added
                ops_config[op_name] = pulse_name
                logger.info(f"Adding '{pulse_name}' to QM config...")
                self.add_pulse(pulse, pulse_name)  # getattr gets Pulse
                old_op_parameters = {key: None for key in op_parameters}  # to check eq
                self.set_pulse(pulse, pulse_name, op_parameters, old_op_parameters)
            else:
                old_op_parameters = old_ops.pop(op_name)  # deleted ops stay in old_ops
                if op_parameters != old_op_parameters:  # op updated
                    self.set_pulse(pulse, pulse_name, op_parameters, old_op_parameters)

        if old_ops is not None:
            for old_op_name in old_ops.keys():  # delete any old_ops that remain
                del ops_config[old_op_name]
                logger.info(f"Deleting {mode} operation '{old_op_name}'...")
                self.delete_pulse(self.get_pulse_name(mode.name, old_op_name))

    def get_pulse_name(self, mode_name: str, op_name: str) -> str:
        """ """
        return mode_name + "." + op_name

    def get_wf_name(self, pulse_name: str, key: str) -> str:
        """ """
        return pulse_name + ".waveform." + key

    def set_pulse(
        self,
        pulse: Pulse,
        pulse_name: str,
        new_op: dict[str, Any],
        old_op: dict[str, Any],
    ) -> None:
        """ """
        pulse_config = self["pulses"][pulse_name]

        if pulse.type_ != pulse_config["operation"]:
            logger.error(f"Forbidden to change {pulse_name} pulse type")
            raise ValueError(f"Forbidden: {pulse.type_} -> {pulse_config['operation']}")
        elif "single" in pulse_config["waveforms"] and pulse.has_mix_waveforms:
            logger.error(f"Forbidden to change {pulse_name} waveform keyset")
            raise ValueError("Forbidden: {'I', 'Q'} <-> {'single'}")

        new_length, old_length = new_op.pop("length"), old_op.pop("length")
        if new_length != old_length:  # pulse length has changed
            self.set_pulse_length(pulse_name, new_length, old_length)

        if new_op != old_op:  # pulse parameters other than length have changed
            self.set_waveforms(pulse, pulse_name)

        if pulse.type_ == "measurement":  # TODO set only on update
            self.set_integration_weights(pulse, pulse_name)

    def add_pulse(self, pulse: Pulse, pulse_name: str) -> None:
        """ """
        pulse_config = self["pulses"][pulse_name]
        pulse_config["operation"] = pulse.type_

        wf_config = pulse_config["waveforms"]
        if pulse.has_mix_waveforms:
            wf_config["I"] = self.get_wf_name(pulse_name, "I")
            wf_config["Q"] = self.get_wf_name(pulse_name, "Q")
        else:
            wf_config["single"] = self.get_wf_name(pulse_name, "single")

        if pulse_config["operation"] == "measurement":
            pulse_config["digital_marker"] = RO_DIGITAL_MARKER
            self["digital_waveforms"][RO_DIGITAL_MARKER]["samples"] = RO_DIGITAL_SAMPLES

    def delete_pulse(self, pulse_name: str) -> None:
        """ """
        for wf_name in self["pulses"][pulse_name]["waveforms"].values():
            del self["waveforms"][wf_name]

        for iw_name in self["pulses"][pulse_name]["integration_weights"].values():
            del self["integration_weights"][iw_name]

        del self["pulses"][pulse_name]

    def set_pulse_length(self, pulse_name: str, new_len: int, old_len: int) -> None:
        """ """
        try:
            length = int(new_len)
        except (TypeError, ValueError) as e:
            logger.exception(f"Invalid {pulse_name} length, must be {int}")
            raise SystemExit("Failed to set pulse len in QM config, exiting...") from e
        else:
            l_min = MIN_PULSE_LEN
            if length % CLOCK_CYCLE != 0 or length < l_min:
                logger.error(f"Length must be int multiple of {CLOCK_CYCLE} >= {l_min}")
                raise ValueError(f"Invalid {pulse_name} length")
            self["pulses"][pulse_name]["length"] = length
            logger.success(f"Set '{pulse_name}' length from {old_len} to {length}")

    def set_waveforms(self, pulse: Pulse, pulse_name: str) -> None:
        """ """
        if isinstance(pulse, ConstantPulse):
            wf_type, samples_key = "constant", "sample"
            pulse_samples = (BASE_AMP * pulse.ampx, 0.0)
        else:
            wf_type, samples_key = "arbitrary", "samples"
            pulse_samples = pulse.samples

        if pulse.has_mix_waveforms:
            for key in ("I", "Q"):
                wave = pulse_samples[0] if key == "I" else pulse_samples[1]
                self.set_waveform(pulse_name, key, wf_type, samples_key, wave)
        else:  # set single waveform
            wave = pulse_samples[0] if wf_type == "constant" else pulse_samples
            self.set_waveform(pulse_name, "single", wf_type, samples_key, wave)

    def set_waveform(
        self,
        pulse_name: str,
        wf_key: str,
        wf_type: str,
        samples_key: str,
        wave: tuple[Union[np.ndarray, float]],
    ) -> None:
        """ """
        wf_name = self.get_wf_name(pulse_name, wf_key)
        wf_config = self["waveforms"][wf_name]
        wf_config["type"] = wf_type

        if wf_type == "constant":
            if not V_MIN < wave < V_MAX:
                logger.error(f"{wf_name} sample {wave} out of bounds")
                raise ValueError(f"Out of bounds ({V_MIN}, {V_MAX})")
            else:
                wf_config[samples_key] = wave
                logger.success(f"Set {wf_name} sample = {wave}")
        elif wf_type == "arbitrary":
            min_, max_ = min(wave), max(wave)
            if min_ <= V_MIN or max_ >= V_MAX:
                logger.error(f"One of {wf_name} samples ({min_}, {max_}) out of bounds")
                raise ValueError(f"Out of bounds ({V_MIN}, {V_MAX})")
            else:
                wf_config[samples_key] = wave
                logger.success(f"Set {len(wave)} samples for {wf_name}")

    def get_iw_name(self, pulse_name: str, iw_key: str) -> str:
        """ """
        return pulse_name + "." + iw_key

    def set_integration_weights(self, pulse: Pulse, pulse_name: str) -> None:
        """ """
        iw_dict = pulse.integration_weights
        for iw_key, iw in iw_dict:
            iw_name = self.get_iw_name(pulse_name, iw_key)
            self["pulses"][pulse_name]["integration_weights"][iw_key] = iw_name
            self["integration_weights"][iw_name] = iw
        logger.success(f"Set integration weights for {pulse_name}")


class QMConfigBuilder:
    """ """

    def __init__(self, *modes: Mode) -> None:
        """ """
        self._modes: set[Mode] = set()
        self._state_map: dict[str, Union[None, dict[str, Any]]] = dict()
        self._check_modes(*modes)
        self._config: QMConfig = QMConfig()
        logger.info(f"Call `.config` to build QM config for {self._modes}")

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}{self._modes}"

    def _check_modes(self, *modes: Mode) -> None:
        """ """
        for mode in modes:
            if not isinstance(mode, Mode):
                logger.error(f"All QMConfigBuilder init *args must be of {Mode}")
                raise SystemExit("Failed to initialize QMConfigBuilder, exiting...")
            self._modes.add(mode)
            self._state_map[mode.name] = None

        if len(self._modes) != len(modes):
            logger.error(f"Mode names must be unique, found duplicate name in {modes}")
            raise SystemExit("Failed to initialize QMConfigBuilder, exiting...")

    @property  # qm config getter
    def config(self) -> dict[str, Any]:
        """ """
        if not self._config:  # build QMConfig for the first time
            logger.info("Initializing QM config...")
            self._config.set_version()
            self._config.set_controllers()
            self._config.set_mixers(*self._modes)  # unpacking set -> tuple
        self._build_config()
        logger.info("Done building QM config!")
        return self._config

    def _build_config(self) -> None:
        """ """
        for mode in self._modes:
            logger.info(f"Building QMConfig for {mode}...")
            curr_state = mode.parameters  # curr means current
            prev_state = self._state_map[mode.name]  # prev means previous
            for parameter in curr_state:  # build config only if parameter value changed
                curr_value = curr_state[parameter]
                prev_value = None if prev_state is None else prev_state[parameter]
                if curr_value != prev_value and parameter in QMConfig.setters:
                    logger.info(f"Updating {mode} {parameter}...")
                    getattr(self._config, QMConfig.setters[parameter])(mode, prev_value)
                elif not parameter in QMConfig.setters:
                    logger.warning(f"Unrecognized parameter '{parameter}'")
            self._state_map[mode.name] = curr_state  # update prev state for next build
