""" g e state discriminator """

from qm.QuantumMachinesManager import QuantumMachinesManager
from qcrew.control import Stagehand
from qcrew.helpers.state_discriminator.TwoStateDiscriminator import (
    TwoStateDiscriminator,
)
import matplotlib.pyplot as plt
from qm import qua
import numpy as np
import yaml

reps = 1000

if __name__ == "__main__":

    with Stagehand() as stage:

        qmm = stage._qmm
        old_config = stage.QM.get_config()
        qubit, qubit_name = stage.modes[0], stage.modes[0].name
        rr, rr_name = stage.modes[1], stage.modes[1].name

        # print("====================")
        # print(yaml.dump(qubit.operations))
        # print("====================")
        # print(yaml.dump(rr.operations))
        # print("====================")
        # print(yaml.dump(old_config))
        # print("====================")
        # print(old_config["integration_weights"].keys())
        # print(old_config['integration_weights']['RR.readout_pulse.iw_i'])
        # print(old_config['integration_weights']['RR.readout_pulse.iw_q'])

        readout_pulse = "readout_pulse"
        pi_pulse = "pi"
        metadata = {
            "wait_time": 200000,
            "reps": 1000,
            "integw_cos": "iw_i",
            "integw_sin": "iw_q",
        }

        # Gaussian Mixture Method
        train1 = TwoStateDiscriminator(
            qmm=qmm,
            config=old_config,
            resonator=rr_name,
            resonator_pulse=readout_pulse,
            qubit=qubit_name,
            qubit_pulse=pi_pulse,
            analog_input=None,  # "out1" by default
            path="weights/ge_discriminator_params_gmm.npz",
            metadata=metadata,
        )

        train1.train(plot=True, simulate=False, correction_method="gmm")
        # train1.test_after_train(simulate=False)

        # Averaging

        # Median

# get updated config
# qmm = QuantumMachinesManager()
# m = qmm.open_qm(updated_config)