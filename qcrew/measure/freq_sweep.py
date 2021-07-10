""" """

from qcrew.control.stage import Stagehand

# insert helper method to plot and show sweep

if __name__ == " __main__":
    stghand = Stagehand()  # init instrument client to mediate between server and user
    stg = stghand.link("QUBIT", "RR", "SA")  # stage dict contains instrument proxies
    qubit, rr, sa = stg["QUBIT"], stg["RR"], stg["SA"]  # unpack stage dict
    freq1, amp1 = sa.sweep(center=qubit.lo_freq, span=250e6)
    freq2, amp2 = sa.sweep(center=rr.lo_freq, span=250e6)
    # call helper method to plot and show sweep
