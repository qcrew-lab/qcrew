from qcrew.control.instruments.vaunix.labbrick import LabBrick
from qcrew.control.instruments.signal_hound.sa124 import Sa124

lb = LabBrick(id=25331, frequency=5e9, power=15)
sa = Sa124(id=19184645)