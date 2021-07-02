""" """

from qm.qua import infinite_loop_, play, program  # TODO

mdata = {
    
}

with program() as mixer_tuning:
    with infinite_loop_():
        play(mdata["op_name"], mdata["mode_name"])
