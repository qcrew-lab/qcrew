""" """

from qcrew.control.stage import Stagehand

# insert helper method to plot and show sweep

if __name__ == " __main__":
    stghand = Stagehand()  # init instrument client to mediate between server and user
    stg = stghand.link("QUBIT", "RR", "SA")  # stage dict contains instrument proxies
    qubit, rr, sa = stg["QUBIT"], stg["RR"], stg["SA"]  # unpack stage dict
    # call helper method to plot and show sweep
