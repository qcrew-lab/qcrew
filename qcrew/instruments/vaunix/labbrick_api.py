"""
API for communicating with Vaunix Signal Generator LMS (LabBrick).
"""
from ctypes import CDLL, c_int
from pathlib import Path
from typing import Union, NoReturn

# ------------------------------------- Driver -----------------------------------------
DLL_NAME = "vnx_fmsynth.dll"  # dll must be in the same directory as this driver
PATH_TO_DLL = Path(__file__).resolve().parent / DLL_NAME  # returns Path object
VNX = CDLL(str(PATH_TO_DLL))  # cast Path to string

# ------------------------------------- Globals ----------------------------------------
FREQ_SCALAR = 10.0  # frequency is encoded as an integer of 10Hz steps
POW_SCALAR = 0.25  # power level is encoded as an integer of 0.25dB steps

# ------------------------------------- Functions --------------------------------------
vnx_set_rf_on = VNX.fnLMS_SetRFOn
vnx_set_use_internal_ref = VNX.fnLMS_SetUseInternalRef


def vnx_connect_to_device(serial_number: int) -> int:
    VNX.fnLMS_SetTestMode(False)  # we are using actual hardware

    num_devices = VNX.fnLMS_GetNumDevices()
    if num_devices == 0:
        raise ConnectionError("No LabBricks available to connect")

    device_array = (c_int * num_devices)()  # initialize array
    VNX.fnLMS_GetDevInfo(device_array)  # fill array with info of all available devices
    serial_numbers = [  # get serial numbers of all available devices
        VNX.fnLMS_GetSerialNumber(device_array[i]) for i in range(num_devices)
    ]

    if serial_number in serial_numbers:
        device_handle = device_array[serial_numbers.index(serial_number)]
        status_code = VNX.fnLMS_InitDevice(device_handle)
        if status_code != 0:  # non-zero return values indicate initialization error
            raise ConnectionError("Failed to open LabBrick {}".format(serial_number))
        return device_handle

    raise ConnectionError("LabBrick with serial no. {} not found".format(serial_number))


def vnx_close_device(device_handle: int) -> NoReturn:
    status_code = VNX.fnLMS_CloseDevice(device_handle)
    if status_code != 0:  # non-zero return values indicate disconnection error
        raise ConnectionError("Failed to close LabBrick")


def vnx_get_max_frequency(device_handle: int) -> float:
    return VNX.fnLMS_GetMaxFreq(device_handle) * FREQ_SCALAR


def vnx_get_min_frequency(device_handle: int) -> float:
    return VNX.fnLMS_GetMinFreq(device_handle) * FREQ_SCALAR


def vnx_get_frequency(device_handle: int) -> float:
    frequency = VNX.fnLMS_GetFrequency(device_handle) * FREQ_SCALAR
    if frequency < 0:  # negative return values indicate error
        raise ValueError("Got bad frequency value {:.7e} Hz".format(frequency))
    return frequency


def vnx_set_frequency(device_handle: int, new_frequency: Union[int, float]) -> NoReturn:
    if not isinstance(new_frequency, (int, float)):
        raise TypeError("Expect {}, {}; got {}".format(int, float, type(new_frequency)))

    frequency_steps = int(new_frequency / FREQ_SCALAR)
    status_code = VNX.fnLMS_SetFrequency(device_handle, frequency_steps)

    if status_code != 0:  # non-zero return values indicate error
        minimum_frequency = vnx_get_min_frequency(device_handle)
        maximum_frequency = vnx_get_max_frequency(device_handle)
        if not minimum_frequency <= new_frequency <= maximum_frequency:
            raise ValueError(
                "Frequency {:.7E} out of bounds; min: {:.2E}, max: {:.2E}".format(
                    new_frequency, minimum_frequency, maximum_frequency
                )
            )
        else:
            raise ConnectionError(
                "Got bad response {}, check LabBrick connection".format(status_code)
            )

    return float(new_frequency)


def vnx_get_max_power(device_handle: int) -> float:
    return VNX.fnLMS_GetMaxPwr(device_handle) * POW_SCALAR


def vnx_get_min_power(device_handle: int) -> float:
    return VNX.fnLMS_GetMinPwr(device_handle) * POW_SCALAR


def vnx_get_power(device_handle: int) -> float:
    power = VNX.fnLMS_GetAbsPowerLevel(device_handle) * POW_SCALAR
    if power < -1e3:  # return values more negative than min power indicate read error
        raise ValueError("Got bad power value {} dBm".format(power))
    return power


def vnx_set_power(device_handle: int, new_power: Union[int, float]) -> NoReturn:
    if not isinstance(new_power, (int, float)):
        raise TypeError("Expect {}, {}; got {}".format(int, float, type(new_power)))

    power_level = int(new_power / POW_SCALAR)
    status_code = VNX.fnLMS_SetPowerLevel(device_handle, power_level)

    if status_code != 0:  # non-zero return values indicate error
        minimum_power = vnx_get_min_power(device_handle)
        maximum_power = vnx_get_max_power(device_handle)
        if not minimum_power <= new_power <= maximum_power:
            raise ValueError(
                "Power {} out of bounds; min: {}, max: {}".format(
                    new_power, minimum_power, maximum_power
                )
            )
        else:
            raise ConnectionError(
                "Got bad response {}, check LabBrick connection".format(status_code)
            )

    return float(new_power)
