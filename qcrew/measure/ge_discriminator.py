""" g e state discriminator """

from qcrew.control import Stagehand
from qcrew.helpers.state_discriminator.TwoStateDiscriminator import (
    TwoStateDiscriminator,
)
from qcrew.helpers.state_discriminator.simulate_configuration import (
    config as sim_config,
)

import matplotlib.pyplot as plt
from qm import qua
import numpy as np
import yaml
from pathlib import Path

save_path = Path("C:\\Users\\qcrew\\qcrew\\data")

if __name__ == "__main__":

    with Stagehand() as stage:

        project_name = stage.project_name
        save_path = save_path / project_name

        qmm = stage._qmm
        old_config = stage.QM.get_config()
        qubit, qubit_name = stage.modes[0], stage.modes[0].name
        rr, rr_name = stage.modes[1], stage.modes[1].name

        print(rr.int_freq)
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
            "reps": 10000,
            "integw_cos": "iw_i",
            "integw_sin": "iw_q",
        }

        # Simulation
        train0 = TwoStateDiscriminator(
            qmm,
            config=sim_config,
            path=save_path / "simulated_ge_discriminator_params_gmm.npz",
        )

        train0.train(plot=True, simulate=True, correction_method="none", reps=100)
        # train0.test_after_train(simulate=True)

        # Averaging
        # train1 = TwoStateDiscriminator(
        #     qmm=qmm,
        #     config=old_config,
        #     resonator=rr_name,
        #     resonator_pulse=readout_pulse,
        #     qubit=qubit_name,
        #     qubit_pulse=pi_pulse,
        #     analog_input=None,  # "out1" by default
        #     path=save_path / "ge_discriminator_params_gmm.npz",
        #     metadata=metadata,
        # )

        # train1.train(plot=True, simulate=False, correction_method="none")
        # train1.test_after_train(simulate=False)

        # Averaging

        # Median

# get updated config
# qmm = QuantumMachinesManager()
# m = qmm.open_qm(updated_config)
