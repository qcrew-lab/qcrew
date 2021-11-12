import numpy as np
from qm.qua import *
from copy import deepcopy


class DCoffsetCalibrator:
    @staticmethod
    def _update_config(config, qe, freq, pulse_length=1e6):
        config["pulses"]["dc_offset_readout_pulse"] = {
            "operation": "measurement",
            "length": pulse_length,
            "waveforms": {
                "I": "dc_offset_zero_wf",
                "Q": "dc_offset_zero_wf",
            },
            "digital_marker": "dc_offset_ON",
        }
        config["digital_waveforms"]["dc_offset_ON"] = {"samples": [(1, 0)]}
        config["waveforms"]["dc_offset_zero_wf"] = {"type": "constant", "sample": 0.0}
        config["elements"][qe]["operations"][
            "dc_offset_readout"
        ] = "dc_offset_readout_pulse"
        config["elements"][qe]["intermediate_frequency"] = freq
        config["elements"][qe]["outputs"] = {"out1": ("con1", 1), "out2": ("con1", 2)}
        config["mixers"][config["elements"][qe]["mixInputs"]["mixer"]][0][
            "intermediate_frequency"
        ] = freq

        print(
            f"ATTENTION: Using the mixer at the 0'th position of {config['elements'][qe]['mixInputs']['mixer']} to "
            f"calibrate DC offset."
        )

        con_name = config["elements"][qe]["outputs"]["out1"][0]
        config["controllers"][con_name]["analog_inputs"] = {
            1: {"offset": 0.0},
            2: {"offset": 0.0},
        }

        return config

    @staticmethod
    def update_dc_offset(
        qe: str, offset: float, config: dict, analog_input: int = 1
    ) -> dict:
        config = deepcopy(config)

        con_name = config["elements"][qe]["outputs"]["out1"][0]
        if analog_input == 1:
            config["controllers"][con_name]["analog_inputs"][analog_input] = {
                "offset": offset
            }
        elif analog_input == 1:
            config["controllers"][con_name]["analog_inputs"][analog_input] = {
                "offset": offset
            }
        else:
            raise ValueError(
                "The analog input {} does not exist in the configuration.".format(
                    analog_input
                )
            )
        return config

    @staticmethod
    def calibrate(qmm, config: dict, qe: str) -> dict:
        """
        Returns the offset that should be applied for the analog inputs of each controller.
        Assumes that when nothing is played there should be zero incoming signal.

        Args:
        qmm: the QuantumMachineManager to execute the program on
        config: the configuration
        qe: quantum element name

        Return:
        A dictionary whose key is the controller name and item is a tuple of two port offsets.
        """
        config = deepcopy(config)

        with program() as cal_dc:

            adc = declare_stream(adc_trace=True)
            reset_phase(qe)
            measure("dc_offset_readout", qe, adc)

            with stream_processing():
                adc.input1().save_all("adc1")
                adc.input2().save_all("adc2")

        freq = config["elements"][qe]["intermediate_frequency"]

        offsets = {}
        qm = qmm.open_qm(DCoffsetCalibrator._update_config(config, qe, freq))
        job = qm.execute(cal_dc)
        job.result_handles.wait_for_all_values()

        adc1 = np.mean(job.result_handles.get("adc1").fetch_all()["value"])
        adc2 = np.mean(job.result_handles.get("adc2").fetch_all()["value"])

        con_name = config["elements"][qe]["outputs"]["out1"][0]
        offset1 = -adc1 * (2 ** -12)
        offset2 = -adc2 * (2 ** -12)
        
        print("DC offsets to apply:")
        print(f"input 1 on {con_name}: ", offset1)
        print(f"input 2 on {con_name}: ", offset2)

        return (offset1, offset2)


