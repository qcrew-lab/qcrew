""" """

import numpy as np

from qcrew.codebase.instruments.instrument import PhysicalInstrument
from qcrew.codebase.instruments.signal_hound.sa_api import (
    SA_AVERAGE,
    SA_FALSE,
    SA_IDLE,
    SA_LOG_SCALE,
    SA_LOG_UNITS,
    SA_RBW_SHAPE_FLATTOP,
    SA_REF_EXTERNAL_IN,
    SA_SWEEPING,
    SA_TRUE,
    sa_close_device,
    sa_config_acquisition,
    sa_config_center_span,
    sa_config_level,
    sa_config_proc_units,
    sa_config_RBW_shape,
    sa_config_sweep_coupling,
    sa_get_sweep_64f,
    sa_initiate,
    sa_open_device_by_serial,
    sa_query_sweep_info,
    sa_set_timebase,
)

# ----------------------------------- Globals ----------------------------------
# dict containing serial numbers and device handles of connected SAs
# key is serial number (int) and value is device handle (int)
ACTIVE_SA_CONNECTIONS = dict()

# detector parameter decides if overlapping results from signal processing
# should be averaged (`SA_AVERAGE`) or if minimum and maximum values should be
# maintained (`SA_MIN_MAX`)
DETECTOR = SA_AVERAGE

# scale parameter changes units of returned amplitudes. Use `SA_LOG_SCALE` for
# dBm, `SA_LIN_SCALE` for millivolts, `SA_LOG_FULL_SCALE` and
# `SA_LIN_FULL_SCALE` for amplitudes to be returned from the full scale input
SCALE = SA_LOG_SCALE

# Specify the RBW filter shape, which is achieved by changing the window
# function. When specifying SA_RBW_SHAPE_FLATTOP, a custom bandwidth flat-top
# window is used measured at the 3dB cutoff point. When specifying
# SA_RBW_SHAPE_CISPR, a Gaussian window with zero-padding is used to achieve
# the specified RBW. The Gaussian window is measured at the 6dB cutoff point.
RBW_SHAPE = SA_RBW_SHAPE_FLATTOP

# specify units for video processing. For “average power” measurements,
# SA_POWER_UNITS should be selected. For cleaning up an amplitude modulated
# signal, SA_VOLT_UNITS would be a good choice. To emulate a traditional
# spectrum analyzer, select SA_LOG_UNITS. To minimize processing power and
# bypass video bandwidth processing, select SA_BYPASS.
VID_PROCESSING_UNITS = SA_LOG_UNITS

# image reject determines whether software image reject will be performed.
# generally, set reject to true for continuous signals, and false to catch
# short duration signals at a known frequency.
DOES_IMAGE_REJECT = SA_TRUE

# ----------------------- Constructor argument names ---------------------------
NAME = "name"  # gettable
SERIAL_NUMBER = "serial_number"  # gettable

# frequency sweep center in Hz
CENTER = "center"  # gettable and settable
DEFAULT_CENTER = 8e9
MAX_CENTER = 13e9  # set by vendor in sa_api.h
MIN_CENTER = 100e3  # set by vendor in sa_api.h

# frequency sweep span in Hz
SPAN = "span"  # gettable and settable
DEFAULT_SPAN = 2e9
MIN_SPAN = 1.0  # set by vendor in sa_api.h

# resolution bandwidth in Hz. Available values are [0.1Hz-100kHz], 250kHz, 6MHz.
# see _is_valid_rbw() for exceptions to available values.
# definition: amplitude value for each frequency bin represents total energy
# from rbw / 2 below and above the bin's center.
RBW = "rbw"  # gettable and settable
DEFAULT_RBW = 250e3

# reference power level of device in dBm.
# set it at or slightly about your expected input power for best sensitivity.
REF_POWER = "ref_power"  # gettable and settable
DEFAULT_REF_POWER = 0
MAX_REF_POWER = 20  # in dBm, set by vendor in sa_api.h

# ---------------------------------- Class -------------------------------------
class Sa124(PhysicalInstrument):
    """
    SA124. TODO - WRITE CLASS DOCU
    """

    # pylint: disable=too-many-arguments
    # this is a physical instrument and requires all these arguments for proper
    # initialisation in frequency sweep mode.
    def __init__(
        self,
        name: str,
        serial_number: int,
        center: float = DEFAULT_CENTER,
        span: float = DEFAULT_SPAN,
        rbw: float = DEFAULT_RBW,
        ref_power: float = DEFAULT_REF_POWER,
    ):
        # TODO use try catch block in case device not authenticated
        print("Trying to initialize " + name + ", will take about 5s...")
        self._device_handle = self._connect(serial_number)
        super().__init__(name=name, uid=serial_number)
        print("Connnected to SA124B " + str(self._uid))

        self._center = center
        self._span = span
        self._rbw = rbw
        self._ref_power = ref_power
        self._initialize()

    def _create_yaml_map(self):
        yaml_map = {
            NAME: self._name,
            SERIAL_NUMBER: self._uid,
            CENTER: self._center,
            SPAN: self._span,
            RBW: self._rbw,
            REF_POWER: self._ref_power,
        }
        return yaml_map

    def _connect(self, uid: int):
        try:
            device_handle = sa_open_device_by_serial(uid)["handle"]
            ACTIVE_SA_CONNECTIONS[uid] = device_handle
            return device_handle
        except RuntimeError as runtime_error:
            if uid in ACTIVE_SA_CONNECTIONS:
                print("You are trying to open an already open SA")
                print("PLEASE DO NOT DO THIS AGAIN WTF")
                device_handle = ACTIVE_SA_CONNECTIONS[uid]
                return device_handle
            else:
                raise runtime_error

    def _initialize(self):
        # this group of settings is set to global default values
        # always use external 10MHz reference
        sa_set_timebase(self._device_handle, SA_REF_EXTERNAL_IN)
        # configure acquisition settings
        sa_config_acquisition(self._device_handle, DETECTOR, SCALE)
        # configure rbw filter shape
        sa_config_RBW_shape(self._device_handle, RBW_SHAPE)
        # configure video processing unit type
        sa_config_proc_units(self._device_handle, VID_PROCESSING_UNITS)

        # sweep parameters are set to user defined values, if given
        # else set to default values
        self._configure_sweep(
            center=self._center,
            span=self._span,
            rbw=self._rbw,
            ref_power=self._ref_power,
        )

    def _is_valid_rbw(self, rbw: float):
        # TODO remove hard coding, do proper logging and error handling, DRY
        start_freq = self._center - (self._span / 2)

        # these two conditions are obtained from the manual
        if (
            self._span >= 100e6 or (self._span > 200e3 and start_freq < 16e6)
        ) and rbw < 6.5e3:
            is_valid_rbw = False
        elif (
            (0.1 <= rbw <= 100e3)
            or (rbw == 250e3)
            or (rbw == 6e6 and start_freq >= 200e6 and self._span >= 200e6)
        ):
            is_valid_rbw = True
        else:
            is_valid_rbw = False

        if not is_valid_rbw:
            print("Bad RBW value given, rbw set to default " + str(DEFAULT_RBW))

        return is_valid_rbw

    def _configure_sweep(self, **sweep_parameters):
        # device must be in idle mode before it is configured
        # the third argument is an inconsequential flag that can be ignored
        sa_initiate(self._device_handle, SA_IDLE, SA_FALSE)

        if "center" in sweep_parameters:
            new_center = sweep_parameters["center"]
            if MIN_CENTER <= new_center <= MAX_CENTER:
                self._center = new_center
            else:
                raise ValueError(
                    "Center out of bounds, must be between "
                    + str(MIN_CENTER)
                    + "-"
                    + str(MAX_CENTER)
                )

        if "span" in sweep_parameters:
            new_span = sweep_parameters["span"]
            if new_span < MIN_SPAN:
                raise ValueError(
                    "Span out of bounds, must be greater than " + str(MIN_SPAN)
                )
            else:
                self._span = new_span

        sa_config_center_span(self._device_handle, self._center, self._span)

        if "rbw" in sweep_parameters:
            new_rbw = sweep_parameters["rbw"]
            if self._is_valid_rbw(new_rbw):
                self._rbw = new_rbw
            else:
                self._rbw = DEFAULT_RBW
            sa_config_sweep_coupling(
                self._device_handle, self._rbw, self._rbw, DOES_IMAGE_REJECT
            )

        if "ref_power" in sweep_parameters:
            new_ref_power = sweep_parameters["ref_power"]
            if new_ref_power > MAX_REF_POWER:
                print("Ref power out of bounds, clamping to " + str(MAX_REF_POWER))
                self._ref_power = MAX_REF_POWER
            else:
                self._ref_power = new_ref_power
            sa_config_level(self._device_handle, self._ref_power)

        # device is ready to sweep
        sa_initiate(self._device_handle, SA_SWEEPING, SA_FALSE)

        #print("Configured sweep! Sweep info: ")
        #print(self.parameters)

    def sweep(self, **sweep_parameters):
        if sweep_parameters:
            self._configure_sweep(**sweep_parameters)

        sweep_info = sa_query_sweep_info(self._device_handle)
        frequencies = [
            sweep_info["start_freq"] + i * sweep_info["bin_size"]
            for i in range(sweep_info["sweep_length"])
        ]
        amplitudes = sa_get_sweep_64f(self._device_handle)["max"]
        return (np.array(frequencies), np.array(amplitudes))

    def disconnect(self):
        sa_close_device(self._device_handle)
        del ACTIVE_SA_CONNECTIONS[self._uid]
        #print(self._name + " disconnected!")

    @property  # sweep parameters getter
    def parameters(self):
        sweep_info = sa_query_sweep_info(self._device_handle)
        sweep_info.pop("status")
        return {
            "start": "{:.7E}".format(sweep_info["start_freq"]),
            CENTER: "{:.7E}".format(self._center),
            SPAN: "{:.3E}".format(self._span),
            "sweep_length": sweep_info["sweep_length"],
            RBW: "{:.3E}".format(self._rbw),
            REF_POWER: self._ref_power,
            "bin_size": "{:.3E}".format(sweep_info["bin_size"]),
        }
