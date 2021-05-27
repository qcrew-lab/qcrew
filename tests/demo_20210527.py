""" Demo of the QMConfigBuilder in action! """

from qcrew.instruments.quantum_machines.qm_config_builder import QMConfigBuilder

# 'qubit' & 'rr' objects will be initialized by the 'InstrumentServer' [WIP]
# they will then be 'borrowed' from the InstrumentServer by the user to run experiments
# for now, let's simulate this by importing 'qubit' and 'rr' from a separate script
from tests.stage_20210527 import qubit, rr, FakeMixerTuner


# qmm = QuantumMachinesManager()  # establish connection to QM
qcb = QMConfigBuilder(qubit, rr)  # initialize the config builder
config = qcb.config  # whenever you run this, you will get the updated QM config


########################################################################################
###################### THE ONE AND ONLY PLACE TO SET ALL THINGS ########################
########### make your changes, then call `qcb.config` prior to opening a QM ############
########################################################################################

FakeMixerTuner().tune(qubit, rr)  # do mixer tuning
qubit.lo_freq = 6.23e9  # this also sets the frequency on the LabBrick!
rr.int_freq = -75e6
rr.time_of_flight = 800

updated_config = qcb.config
# qm = qmm.open_qm(updated_config)
# qm.execute(measurement_script)

qubit.operations["pi"] = {
    
}
########################################################################################
########################################################################################

# stage.save() [WIP]  # run this to want to save all stage parameters to disk
