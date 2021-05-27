""" """

from ctypes import CDLL, c_int, Array
from pathlib import Path

# ------------------------------------- Driver -----------------------------------------
DLL_NAME = "vnx_fmsynth.dll"  # dll must be in the same directory as this driver
PATH_TO_DLL = Path(__file__).resolve().parent / DLL_NAME  # returns Path object
VNX = CDLL(str(PATH_TO_DLL))  # cast Path to string
VNX.fnLMS_SetTestMode(False)  # we are using actual hardware

# ------------------------------------- Globals ----------------------------------------
FREQ_SCALAR = 10.0  # frequency is encoded as an integer of 10Hz steps
POW_SCALAR = 0.25  # power level is encoded as an integer of 0.25dB steps

# -------------------------------------- Methods ---------------------------------------
get_rf_on = VNX.fnLMS_GetRF_On
set_rf_on = VNX.fnLMS_SetRFOn
set_use_internal_ref = VNX.fnLMS_SetUseInternalRef


def connect_to_device(serial_number: int) -> int:
    """ """
    num_devices = _get_num_available_devices()
    device_info_array = _get_devices_info(num_devices)
    serial_numbers = _get_serial_numbers(num_devices, device_info_array)

    if serial_number in serial_numbers:
        device_handle = device_info_array[serial_numbers.index(serial_number)]
        _initialize_device(device_handle)
        return device_handle
    raise ConnectionError(f"LabBrick with {serial_number = } not found")


def _get_num_available_devices() -> int:
    """ """
    num_devices = VNX.fnLMS_GetNumDevices()
    if num_devices == 0:
        raise ConnectionError("No LabBricks available to connect")
    return num_devices


def _get_devices_info(num_devices: int) -> Array:
    """ """
    device_array = (c_int * num_devices)()  # initialize array to hold device info
    VNX.fnLMS_GetDevInfo(device_array)  # fill array with info of all available devices
    return device_array


def _get_serial_numbers(num_devices: int, device_array: Array) -> list:
    """ """
    return [VNX.fnLMS_GetSerialNumber(device_array[i]) for i in range(num_devices)]


def _initialize_device(device_handle: int):
    """ """
    status_code = VNX.fnLMS_InitDevice(device_handle)
    if status_code != 0:  # non-zero return values indicate initialization error
        raise ConnectionError("Failed to open LabBrick")


def close_device(device_handle: int) -> None:
    """ """
    status_code = VNX.fnLMS_CloseDevice(device_handle)
    if status_code != 0:  # non-zero return values indicate disconnection error
        raise ConnectionError("Failed to close LabBrick")


def get_max_frequency(device_handle: int) -> float:
    """ """
    return VNX.fnLMS_GetMaxFreq(device_handle) * FREQ_SCALAR


def get_min_frequency(device_handle: int) -> float:
    """ """
    return VNX.fnLMS_GetMinFreq(device_handle) * FREQ_SCALAR


def get_frequency(device_handle: int) -> float:
    """ """
    frequency = VNX.fnLMS_GetFrequency(device_handle) * FREQ_SCALAR
    if frequency < 0:  # negative return values indicate read error
        raise ConnectionError("Got bad response, check LabBrick connection")
    return frequency


def set_frequency(device_handle: int, new_frequency: float) -> float:
    """ """
    if not isinstance(new_frequency, (int, float)):
        raise TypeError(f"Expect {int} or {float}; got {type(new_frequency)}")

    frequency_steps = int(new_frequency / FREQ_SCALAR)
    status_code = VNX.fnLMS_SetFrequency(device_handle, frequency_steps)
    if status_code == 0:  # success
        return float(new_frequency)
    else:  # non-zero return values indicate error
        _check_frequency_bounds(device_handle, float(new_frequency))
        raise ConnectionError("Got bad response, check LabBrick connection")


def _check_frequency_bounds(device_handle: int, frequency: float) -> None:
    """ """
    min_ = get_min_frequency(device_handle)
    max_ = get_max_frequency(device_handle)
    if not min_ <= frequency <= max_:
        raise ValueError(f"{frequency:.7E = } out of bounds [{min_:.2E}, {max_:.2E}]")


def get_max_power(device_handle: int) -> float:
    """ """
    return VNX.fnLMS_GetMaxPwr(device_handle) * POW_SCALAR


def get_min_power(device_handle: int) -> float:
    """ """
    return VNX.fnLMS_GetMinPwr(device_handle) * POW_SCALAR


def get_power(device_handle: int) -> float:
    """ """
    power = VNX.fnLMS_GetAbsPowerLevel(device_handle) * POW_SCALAR
    if power < -1e5:  # return values more negative than min power indicate read error
        raise ConnectionError("Got bad response, check LabBrick connection")
    return power


def set_power(device_handle: int, new_power: float) -> float:
    """ """
    if not isinstance(new_power, (int, float)):
        raise TypeError(f"Expect {int} or {float}; got {type(new_power)}")

    power_level = int(new_power / POW_SCALAR)
    status_code = VNX.fnLMS_SetPowerLevel(device_handle, power_level)

    if status_code == 0:  # success
        return float(new_power)
    else:  # non-zero return values indicate error
        _check_power_bounds(device_handle, float(new_power))
        raise ConnectionError("Got bad response, check LabBrick connection")


def _check_power_bounds(device_handle: int, power: float) -> None:
    """ """
    min_ = get_min_power(device_handle)
    max_ = get_max_power(device_handle)
    if not min_ <= power <= max_:
        raise ValueError(f"{power = } out of bounds [{min_}, {max_}]")
