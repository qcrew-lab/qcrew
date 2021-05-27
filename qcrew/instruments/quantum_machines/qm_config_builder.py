""" """

from collections import defaultdict
from typing import Any, Callable, Union

import numpy as np
from qcrew.helpers import logger
from qcrew.helpers.pulsemaker import (
    ZERO_WAVEFORM,
    ControlPulse,
    MeasurementPulse,
    PulseType,
    Waveform,
)
from qcrew.instruments.meta import QuantumElement

CONFIG_VERSION = 1
CONTROLLER_NAME = "con1"
CONTROLLER_TYPE = "opx1"
AO_PORT_BOUNDS = (0, 11)  # (min, max), AO means analog output
AI_PORT_BOUNDS = (0, 3)  # (min, max), AI means analog input
VOLTAGE_BOUNDS = (-0.5, 0.5)  # [min, max], for dc offsets
CORRECTION_BOUNDS = (-2.0, 2 - 2 ** -16)  # (min, max), for mixer correction matrix
DEFAULT_DIGITAL_MARKER = "ON"
DEFAULT_DIGITAL_ON_SAMPLES = [(1, 0)]
CLOCK_CYCLE = 4  # in ns

get_mixer_name = lambda e_name: e_name + ".mixer"
get_pulse_name = lambda e_name, op_name: e_name + "." + op_name
get_wf_name = lambda p_name, key: p_name + ".wf." + key  # wf means waveform
get_iw_name = lambda p_name, key: p_name + "." + key  # iw means integration weight

_Mixer = dict[str, dict[str, float]]
_Ops = dict[str, PulseType]
_Pulse = PulseType


class QMConfig(defaultdict):
    """ """

    def __init__(self) -> None:
        """ """
        super().__init__(QMConfig)

    def __repr__(self) -> str:
        """ """
        return repr(dict(self))


def _set_version(config: QMConfig) -> None:
    """ """
    config["version"] = CONFIG_VERSION


def _set_controller_type(config: QMConfig) -> None:
    """ """
    config["controllers"][CONTROLLER_NAME]["type"] = CONTROLLER_TYPE


def _set_default_waveforms(config: QMConfig) -> None:
    """ """
    config["waveforms"]["zero_wf"] = {"type": "constant", "sample": 0.0}


def _check_bounds(value: int, min_: int, max_: int) -> None:
    """ """
    if not min_ < value < max_:
        raise ValueError(f"{value = } out of bounds ({min_}, {max_})")


def _create_ports(config: QMConfig, ports: dict[str, dict[str, int]]) -> None:
    """ """
    for e_name in ports:
        logger.info(f"Setting {e_name} ports to {ports[e_name]}...")
        for port in ports[e_name]:
            try:
                port_value = ports[e_name][port]
                port_number = int(port_value)
                _set_controller_port(config, key=port, value=port_number)
            except ValueError as e:
                logger.exception(f"Invalid {e_name} {port} port {port_value}")
                raise SystemExit("Failed to set ports in QM config, exiting...") from e
            else:
                _set_element_port(config, e_name, key=port, value=port_number)


def _set_controller_port(config: QMConfig, key: str, value: int) -> None:
    """ """
    controller_config = config["controllers"][CONTROLLER_NAME]
    if key in ("I", "Q", "single"):
        if value in controller_config["analog_outputs"]:
            logger.error(f"Analog output port {value} has already been assigned")
            raise ValueError("Duplicate port assignment")
        _check_bounds(value, min_=AO_PORT_BOUNDS[0], max_=AO_PORT_BOUNDS[1])
        controller_config["analog_outputs"][value]["offset"] = 0.0
    elif key == "out":
        if value in controller_config["analog_inputs"]:
            logger.error(f"Analog input port {value} has already been assigned")
            raise ValueError("Duplicate port assignment")
        _check_bounds(value, min_=AI_PORT_BOUNDS[0], max_=AI_PORT_BOUNDS[1])
        controller_config["analog_inputs"][value]["offset"] = 0.0


def _set_element_port(config: QMConfig, e_name: str, key: str, value: int) -> None:
    """ """
    element_config = config["elements"][e_name]
    if key in ("I", "Q"):
        element_config["mixInputs"][key] = (CONTROLLER_NAME, value)
    elif key == "out":
        key = key + str(value)  # valid config keys are "out1" or "out2"
        element_config["outputs"][key] = (CONTROLLER_NAME, value)
    elif key == "single":
        element_config["singleInput"]["port"] = (CONTROLLER_NAME, value)


def _create_mixers(config: QMConfig, ports: dict[str, dict[str, int]]) -> None:
    """ """
    mixer_dict_keys = {"intermediate_frequency", "lo_frequency", "correction"}
    for e_name in ports:
        if set(ports[e_name]) >= {"I", "Q"}:  # if element has mix input ports
            mixer_name = get_mixer_name(e_name)
            logger.info(f"Creating '{mixer_name}'...")
            config["mixers"][mixer_name] = [{key: None for key in mixer_dict_keys}]
            config["elements"][e_name]["mixInputs"]["mixer"] = mixer_name


def _set_mixer(config: QMConfig, e_name: str, new_val: _Mixer, old_val: _Mixer) -> None:
    """ """
    element_config = config["elements"][e_name]
    if "mixInputs" not in element_config:
        logger.warning(f"Ignored mixer defined for element {e_name} with no mix inputs")
        return

    mixer_name = get_mixer_name(e_name)
    analog_outputs_config = config["controllers"]["con1"]["analog_outputs"]
    offsets = new_val["offsets"]
    diff = set(offsets) if old_val is None else (set(offsets) - set(old_val["offsets"]))
    try:
        if "I" in diff:
            i_offset = float(offsets["I"])
            _check_bounds(i_offset, min_=VOLTAGE_BOUNDS[0], max_=VOLTAGE_BOUNDS[1])
            i_port = element_config["mixInputs"]["I"][1]
            analog_outputs_config[i_port]["offset"] = i_offset
        if "Q" in diff:
            q_offset = float(offsets["Q"])
            _check_bounds(i_offset, min_=VOLTAGE_BOUNDS[0], max_=VOLTAGE_BOUNDS[1])
            q_port = element_config["mixInputs"]["Q"][1]
            analog_outputs_config[q_port]["offset"] = q_offset
        if "G" in diff or "P" in diff:
            g_offset, p_offset = float(offsets["G"]), float(offsets["P"])
            correction = _get_mixer_correction_matrix(g_offset, p_offset)
            config["mixers"][mixer_name][0]["correction"] = correction
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid value found in {mixer_name} {offsets = }")
        raise SystemExit("Failed to set mixer offsets in QM config, exiting...") from e
    else:
        logger.success(f"Set {mixer_name} {offsets = }")


def _get_mixer_correction_matrix(gain: float, phase: float) -> list[float]:
    """ """
    cos = np.cos(phase)
    sin = np.sin(phase)
    coeff = 1 / ((1 - gain ** 2) * (2 * cos ** 2 - 1))
    matrix = [(1 - gain) * cos, (1 + gain) * sin, (1 - gain) * sin, (1 + gain) * cos]
    correction_matrix = [float(coeff * x) for x in matrix]
    for value in correction_matrix:
        _check_bounds(value, min_=CORRECTION_BOUNDS[0], max_=CORRECTION_BOUNDS[1])
    return correction_matrix


def _set_lo_freq(config: QMConfig, e_name: str, new_val: float, old_val: float) -> None:
    """ """
    try:
        lo_freq = int(new_val)
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid {e_name} lo freq {new_val}, expect ({int},{float})")
        raise SystemExit("Failed to set lo freq in QM config, exiting...") from e
    else:
        config["elements"][e_name]["mixInputs"]["lo_frequency"] = lo_freq
        config["mixers"][get_mixer_name(e_name)][0]["lo_frequency"] = lo_freq
        logger.success(f"Set {e_name} lo freq from {old_val} to {lo_freq}")


def _set_if(config: QMConfig, e_name: str, new_val: float, old_val: float) -> None:
    """ """
    try:
        int_freq = int(new_val)
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid {e_name} int freq {new_val}, expect ({int},{float})")
        raise SystemExit("Failed to set int freq in QM config, exiting...") from e
    else:
        config["elements"][e_name]["intermediate_frequency"] = int_freq
        config["mixers"][get_mixer_name(e_name)][0]["intermediate_frequency"] = int_freq
        logger.success(f"Set {e_name} int freq from {old_val} to {int_freq}")


def _set_tof(config: QMConfig, e_name: str, new_val: int, old_val: int) -> None:
    """ """
    try:
        tof = int(new_val)  # tof means time_of_flight
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid {e_name} time of flight {new_val}, expect {int}")
        raise SystemExit("Failed to set time of flight in QM config, exiting...") from e
    else:
        if tof % CLOCK_CYCLE != 0:
            tof = CLOCK_CYCLE * round(tof / CLOCK_CYCLE)
            logger.warning(f"Rounded tof to nearest multiple of {CLOCK_CYCLE}")
        config["elements"][e_name]["time_of_flight"] = tof
        logger.success(f"Set {e_name} time of flight from {old_val} to {tof}")


def _set_smearing(config: QMConfig, e_name: str, new_val: int, old_val: int) -> None:
    """ """
    try:
        smearing = int(new_val)
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid {e_name} smearing {new_val}, expect {int}")
        raise SystemExit("Failed to set smearing in QM config, exiting...") from e
    else:
        config["elements"][e_name]["smearing"] = smearing
        logger.success(f"Set {e_name} smearing from {old_val} to {smearing}")


def _set_ops(config: QMConfig, e_name: str, new_val: _Ops, old_val: _Ops) -> None:
    """ """
    symm_diff = set(new_val) if old_val is None else (set(new_val) ^ set(old_val))
    for op_name in symm_diff:  # symm_diff means symmetric difference
        pulse_name = get_pulse_name(e_name, op_name)  # name to be set in QM config
        operations_config = config["elements"][e_name]["operations"]
        if op_name not in new_val:  # op has been removed
            del operations_config[op_name]
            old_pulse = old_val[op_name]
            _del_pulse(config, pulse_name, old_pulse)
            logger.success(f"Deleted {e_name} operation '{op_name}'")
        else:  # op added or updated
            new_pulse = new_val[op_name]
            operations_config[op_name] = pulse_name
            logger.info(f"Setting {e_name} operation '{op_name}'...")
            _set_pulse(config, pulse_name, new_pulse)


def _set_pulse(config: QMConfig, p_name: str, pulse: _Pulse) -> None:
    """ """
    pulse_config = config["pulses"][p_name]
    _set_pulse_len(config, p_name, pulse.length, None)

    for key, waveform in pulse.waveforms.items():
        wf_name = "zero_wf" if waveform == ZERO_WAVEFORM else get_wf_name(p_name, key)
        pulse_config["waveforms"][key] = wf_name
        if wf_name != "zero_wf":
            _set_waveform(config, wf_name, waveform)
        logger.success(f"Set {p_name} '{key}' to {waveform}")

    if isinstance(pulse, MeasurementPulse):
        pulse_config["operation"] = "measurement"
        pulse_config["digital_marker"] = DEFAULT_DIGITAL_MARKER
        _set_digital_waveform(config, DEFAULT_DIGITAL_MARKER)
        for iw_key in set(pulse.iw):
            pulse_config["integration_weights"][iw_key] = get_iw_name(p_name, iw_key)
        _set_integration_weights(config, p_name, pulse)
    elif isinstance(pulse, ControlPulse):
        pulse_config["operation"] = "control"


def _del_pulse(config: QMConfig, p_name: str, pulse: _Pulse) -> None:
    """ """
    for wf_name in config["pulses"][p_name]["waveforms"].values():
        if wf_name != "zero_wf":
            del config["waveforms"][wf_name]

    if isinstance(pulse, MeasurementPulse):
        for iw_key in set(pulse.iw):
            del config["integration_weights"][get_iw_name(p_name, iw_key)]

    del config["pulses"][p_name]


def _set_pulse_len(config: QMConfig, p_name: str, new_val: int, old_val: int) -> None:
    """ """
    try:
        new_len = int(new_val)
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid {p_name} length {new_val}, expect {int}")
        raise SystemExit("Failed to update pulse in QM config, exiting...") from e
    else:
        if new_len % CLOCK_CYCLE != 0:
            new_len = CLOCK_CYCLE * round(new_len / CLOCK_CYCLE)
            logger.warning((f"Rounded pulse len to nearest multiple of {CLOCK_CYCLE}"))
        config["pulses"][p_name]["length"] = new_len
        logger.success(f"Set {p_name} length from {old_val} to {new_len}")


def _set_integration_weights(config: QMConfig, p_name: str, pulse: _Pulse) -> None:
    """ """
    for key, fns in pulse.iw.items():
        iw_config = config["integration_weights"][get_iw_name(p_name, key)]
        try:
            iw_config["cosine"] = fns[0](int(pulse.length / CLOCK_CYCLE))
            iw_config["sine"] = fns[1](int(pulse.length / CLOCK_CYCLE))
        except (TypeError, IndexError) as e:
            logger.exception(f"Invalid integration weight '{key}' generator {fns = }")
            raise SystemExit("Failed to set integration weights, exiting...") from e
    logger.success(f"Set integration weights for {p_name}")


def _set_waveform(config: QMConfig, wf_name: str, waveform: Waveform) -> None:
    """ """
    wf_config = config["waveforms"][wf_name]
    wf_type = "constant" if waveform.is_constant else "arbitrary"
    wf_config["type"] = wf_type

    try:
        if wf_type == "constant":
            sample = float(waveform.samples)
            _check_bounds(sample, min_=VOLTAGE_BOUNDS[0], max_=VOLTAGE_BOUNDS[1])
            wf_config["sample"] = sample
        else:
            samples = [float(sample) for sample in waveform.samples]
            _check_bounds(max(samples), min_=VOLTAGE_BOUNDS[0], max_=VOLTAGE_BOUNDS[1])
            _check_bounds(min(samples), min_=VOLTAGE_BOUNDS[0], max_=VOLTAGE_BOUNDS[1])
            wf_config["samples"] = samples
    except (TypeError, ValueError) as e:
        logger.exception(f"Invalid {waveform} sample(s) obtained")
        raise SystemExit("Failed to set waveforms in QM config, exiting...") from e


def _set_digital_waveform(config: QMConfig, dw_name: str) -> None:
    """ """
    if dw_name not in config["digital_waveforms"]:
        config["digital_waveforms"][dw_name]["samples"] = DEFAULT_DIGITAL_ON_SAMPLES


method_map: dict[str, Callable] = {
    "lo_freq": _set_lo_freq,
    "int_freq": _set_if,
    "mixer": _set_mixer,
    "operations": _set_ops,
    "time_of_flight": _set_tof,
    "smearing": _set_smearing,
}


class QMConfigBuilder:
    """ """

    # instance variable to save the previous state of all elements
    _state_map: dict[str, Union[None, dict[str, Any]]] 

    def __init__(self, *elements: QuantumElement) -> None:
        """ """
        self._elements: set[QuantumElement] = self._check_elements(*elements)
        self._state_map = {e.name: None for e in self._elements}  # {e.name: e.params}
        self._config: QMConfig = None  # set on first `.config` call by _create_config()
        logger.info(f"Call `.config` to build QM config for {self._elements}")

    def _check_elements(self, *elements: QuantumElement) -> set[QuantumElement]:
        """ """
        element_names = set()
        for element in elements:  # all elements must be of QuantumElement
            if not isinstance(element, QuantumElement):
                logger.error(f"__init_() *args must be of {QuantumElement}")
                raise SystemExit("Failed to initialize QMConfigBuilder, exiting...")

            element_name = element.name
            if element_name not in element_names:  # all element names must be unique
                element_names.add(element_name)
            else:
                logger.error(f"Found duplicate {element_name = }, names must be unique")
                raise SystemExit("Failed to initialize QMConfigBuilder, exiting...")
        return set(elements)

    @property  # qm config getter
    def config(self) -> dict[str, Any]:
        """ """
        if self._config is None:  # user has called `.config` for the first time
            logger.info(f"Creating QM config for {self._elements}...")
            self._create_config()
        self._update_config()
        logger.info("QM config is ready!")
        return self._config

    def _create_config(self) -> None:
        """ """
        self._config = QMConfig()
        _set_version(self._config)  # set non-element related config fields
        _set_controller_type(self._config)
        _set_default_waveforms(self._config)

        # set non-modifiable element fields - "ports" and "mixers" (if applicable)
        ports = {e.name: e.ports for e in self._elements}  # e means element
        _create_ports(self._config, ports)
        _create_mixers(self._config, ports)

    def _update_config(self) -> None:
        """ """
        for element in self._elements:
            logger.info(f"Checking for updates to {element}...")
            e_name = element.name  # e means element
            curr_state = element.parameters  # curr means current
            prev_state = self._state_map[e_name] # prev means previous
            for param in curr_state:
                curr_value = curr_state[param]
                prev_value = None if prev_state is None else prev_state[param]
                if curr_value != prev_value:  # update config if param value changed
                    method_map[param](self._config, e_name, curr_value, prev_value)
            self._state_map[e_name] = curr_state  # update prev state for next update
