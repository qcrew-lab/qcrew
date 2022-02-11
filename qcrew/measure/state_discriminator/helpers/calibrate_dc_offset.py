import matplotlib.pyplot as plt
from qcrew.control import Stagehand
import qcrew.control.pulses as qcp
from qm import qua
import numpy as np

""" calilbrate DC offset for optimized readout """


def get_qua_program(rr):

    with qua.program() as cal_dc:

        adc = qua.declare_stream(adc_trace=True)
        qua.reset_phase(rr.name)
        qua.measure("dc_offset_op", rr.name, adc)

        with qua.stream_processing():
            adc.input1().save("adc")

    return cal_dc


if __name__ == "__main__":
    with Stagehand() as stage:

        # Reset DC offset of readout mode to be calibrated
        rr = stage.RR
        rr.mixer_offsets = {"out": 0}

        # add new operation for dc offset calibration
        # rr.operations = {"dc_offset_op": qcp.ReadoutPulse()}
        integration_weights = qcp.ConstantIntegrationWeights()
        readout_pulse = qcp.ReadoutPulse(
            length=int(10000),
            const_length=int(10000),
            ampx=0,
            integration_weights=integration_weights,
        )
        rr.operations = {"dc_offset_op": readout_pulse}
        print(rr.operations)

        # Execute script
        job = stage.QM.execute(get_qua_program(rr))  # play IF to mode

        handle = job.result_handles
        handle.wait_for_all_values()
        adc_avg = np.mean(handle.get("adc").fetch_all())
        dc_offset = -adc_avg * (2 ** -12)

        # Update DC offset
        rr.mixer_offsets = {"out": dc_offset}
