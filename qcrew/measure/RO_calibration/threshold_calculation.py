""" Readout integration weights training for single-shot readout """

from qcrew.control.instruments.meta.readout_trainer import ReadoutTrainer
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.control import Stagehand

if __name__ == "__main__":
    with Stagehand() as stage:
        rr, qubit = stage.RR, stage.QUBIT
        qm = stage.QM

        params = {
            "reps": 10_000,
            "wait_time": 500_000,  # ns 
            "qubit_pi_pulse": "qubit_gaussian_pi_pulse",  # pulse to excite qubit
        }

        # ddrop_params = {
        #     "rr_ddrop_freq": int(-50.4e6),
        #     "rr_ddrop": "ddrop_pulse",
        #     "qubit_ddrop": "ddrop_pulse",
        #     "qubit_ef_mode": stage.QUBIT_EF,
        #     "steady_state_wait": 2000,
        # }

        # ro_trainer = ReadoutTrainer(rr, qubit, qm, ddrop_params=ddrop_params, **params)
        ro_trainer = ReadoutTrainer(rr, qubit, qm, **params)
        threshold, data = ro_trainer.calculate_threshold()

        ## Save data
        db = initialise_database(
            exp_name="threshold_calculation",
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )
        with DataSaver(db) as datasaver:
            # add metadata dictionary
            datasaver.add_metadata(ro_trainer.parameters)

            for mode in ro_trainer.modes:
                datasaver.add_metadata(mode.parameters)

            datasaver.add_multiple_results(data, save=data.keys(), group="data")
