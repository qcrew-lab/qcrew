from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.instruments.vaunix.labbrick import LabBrick
from qcrew.control.modes.qubit import Qubit
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import program, infinite_loop_
from qcrew.control.instruments.mixer_tuner import MixerTuner

qmm = QuantumMachinesManager()
lb_qubit = LabBrick(id=25331, frequency=5e9, power=15)
qubit = Qubit(name="qubit", lo=lb_qubit, int_freq=-50e6, ports={"I": 1, "Q": 2})
qcb = QMConfigBuilder(qubit)
qm = qmm.open_qm(qcb.config)
sa = Sa124(id=19184645)
mxrtnr = MixerTuner(sa, qm, qubit)
mxrtnr.tune()

with program() as qua_test:
    with infinite_loop_():
        qubit.play("constant_pulse")

job = qm.execute(qua_test)
