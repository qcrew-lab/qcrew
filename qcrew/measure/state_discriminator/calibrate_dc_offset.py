
import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np

""" calilbrate DC offset for optimized readout """


def get_qua_program(rr, dc_offset_op):
    
    with qua.program() as cal_dc:

        adc = qua.declare_stream(adc_trace=True)
        qua.reset_phase(rr.name)
        qua.measure(dc_offset_op, rr.name, adc)

        with stream_processing():
            adc.input1().save("adc")
              
    return cal_dc

if __name__ == "__main__":
    with Stagehand() as stage:

        # Reset DC offset of readout mode to be calibrated
        rr = stage.RR
        rr.mixer_offsets = {"out": 0}

        # Execute script
        job = stage.QM.execute(get_qua_program(rr))  # play IF to mode

        handle = job.result_handles
        handle.wait_for_all_values()
        adc_avg = np.mean(handle.get("adc").fetch_all())
        dc_offset = -adc_avg * (2 ** -12)
        
        rr.mixer_offsets = {"out": dc_offset}
    
