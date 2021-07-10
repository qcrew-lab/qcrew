""" """

from qcrew.control.instruments.mixer_tuner import MixerTuner
from qcrew.control.stage import Stagehand

if __name__ == " __main__":
    stghand = Stagehand()  # init instrument client to mediate between server and user
    stg = stghand.link("QUBIT", "RR", "SA")  # stage dict contains instrument proxies
    qubit, rr, sa = stg["QUBIT"], stg["RR"], stg["SA"]  # unpack stage dict
    qm = stghand.get_qm(qubit, rr)  # returns an already configured QM
    mxrtnr = MixerTuner(sa, qm, qubit, rr)  # initialize the new improved MixerTuner
    mxrtnr.tune()  # tunes both lo and sb only if out of tune in 5s per mode
