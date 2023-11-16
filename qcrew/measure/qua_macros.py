import numpy as np
import copy
from qm import qua


class ExpVariable:
    """
    This class holds relevant information for a variable of an experiment, including its QUA variable instance and type, the QUA stream to which send the data, and configurations for data saving.
    """

    def __init__(
        self,
        var=None,
        var_type=None,
        stream=None,
        tag=None,
        sweep=None,
        average=True,
        buffer=True,
        save_all=True,
    ):

        # QUA variable
        self.var = var

        # QUA variable type (int, fixed, bool).
        # Can be updated in configure_sweep()
        self.type = var_type

        # QUA stream to which send values
        self.stream = stream

        # Memory tag for saving values
        self.tag = tag

        # sweep holds the sweep configuration of the variable
        # sweep_type defines the qua loop to be used for iterations
        # buffer_len stores the number of values in the sweep
        self.sweep = None
        self.sweep_type = None
        self.buffer_len = None
        self.configure_sweep(sweep)  # Updates sweep attributes

        # Flag for averaging saved values over repetitions
        self.average = average

        # Flag for buffering saved values
        self.buffer = buffer

        # Flag for saving all values to memory
        self.save_all = save_all

    def configure_sweep(self, sweep):
        """
        Check if the sweep is correctly configured. If so, update buffering, variable type and sweep type accordingly.
        """

        if sweep is None:
            self.sweep = None
            self.sweep_type = None
            self.buffer_len = None
            return

        # Identify the variable type of the sweep
        if all(isinstance(s, bool) for s in sweep):
            var_type = bool
        elif all(isinstance(s, int) for s in sweep):
            var_type = int
        elif all(isinstance(s, (int, float)) for s in sweep):
            var_type = qua.fixed
        else:
            print("Error! Sweep type not identified")  # TODO
            exit()

        # Updates variable type if none is given and check for conflict
        if self.type is None:
            self.type = var_type
        else:
            if self.type != var_type:
                print("Given variable type does not match sweep")  # TODO
                exit()

        # Check if sweep values are given explicitly. In this case, set sweep_type as
        # 'for_each_'. Else, set 'for_'. Update buffer_len accordingly.
        if var_type is bool:
            self.sweep_type = "for_each_"
        elif len(sweep) == 3 and len(np.arange(*sweep)) > 3:
            # If three values are given and these can be used to build a list of evenly
            # spaced values, identify sweep type as 'for_'
            # TODO send message
            self.sweep_type = "for_"
        else:
            self.sweep_type = "for_each_"

        # Define buffer length according to the sweep type
        if self.sweep_type == "for_":
            self.buffer_len = len(np.arange(*sweep))
        if self.sweep_type == "for_each_":
            self.buffer_len = len(sweep)

        self.sweep = sweep

        return


def declare_variables(var_list):
    """
    Calls QUA variable declaration statements. Stores QUA variables in var_list and
    returns it.
    """

    for key in var_list.keys():
        if var_list[key].type is None:
            continue

        var_list[key].var = qua.declare(var_list[key].type)

    return var_list


def declare_streams(var_list):
    """
    Calls QUA stream declaration statements. Stores QUA streams in var_list and
    returns it.
    """
    for key in var_list.keys():
        if var_list[key].tag is None:
            continue

        # Declare stream
        var_list[key].stream = qua.declare_stream()

    return var_list


def stream_results(var_list):
    """
    Calls QUA save statement for each ExpVariable object in var_list. Only saves if a
    stream is defined
    """

    for key, value in var_list.items():
        if value.stream is None:
            continue
        qua.save(value.var, value.stream)


def process_streams(var_list, buffer_len=1):
    """
    Save streamed values to memory.
    """

    for key, value in var_list.items():
        if value.stream is None:
            continue
        stream = copy.deepcopy(value.stream)
        memory_tag = value.tag
        if value.buffer:
            stream = stream.buffer(buffer_len)
        if value.average:
            stream = stream.average()
        if value.save_all:
            stream.save_all(memory_tag)
        else:
            stream.save(memory_tag)


def process_Z_values(I_stream, Q_stream, buffer_len=1):
    """
    Use results from I and Q streams to save processed data to memory. Z_SQ_RAW and Z_SQ_RAW_AVG are used for std error calculation; Z_AVG, for plotting.
    """

    # Is and Qs
    I_raw = I_stream.buffer(buffer_len)
    Q_raw = Q_stream.buffer(buffer_len)  # to reshape result streams
    I_avg = I_raw.average()
    Q_avg = Q_raw.average()

    # we need these two streams to calculate  std err in a single pass
    (I_raw * I_raw + Q_raw * Q_raw).save_all("Z_SQ_RAW")
    (I_raw * I_raw + Q_raw * Q_raw).average().save_all("Z_SQ_RAW_AVG")

    # to live plot latest average
    (I_avg * I_avg + Q_avg * Q_avg).save("Z_AVG")
    # Also save I_avg and Q_avg
    I_avg.save("I_AVG")
    Q_avg.save("Q_AVG")


def QUA_loop(qua_function, sweep_variables):
    """
    Loops a given qua_function. ::sweep_variables:: holds a list of ExpVariable objects for which a sweep is configured. Its order matches the loop nesting order.
    The first variable is assumed to always use qua.for_ loops.
    """

    # Repetition loop
    n = sweep_variables[0]
    v1 = sweep_variables[1]
    v2 = sweep_variables[2]

    n_start, n_stop, n_step = n.sweep
    # Unpack start, stop, step if sweep_type is 'for_'
    if v1.sweep_type == "for_":
        v1_start, v1_stop, v1_step = v1.sweep
    if v2.sweep_type == "for_":
        v2_start, v2_stop, v2_step = v2.sweep

    with qua.for_(n.var, n_start, n.var < n_stop, n.var + n_step):

        # If neither v1 nor v2 sweeps are configured, simply play function
        if v1.sweep is None and v2.sweep is None:
            qua_function()

        # If only v1 sweep is configured
        elif v2.sweep is None:
            if v1.sweep_type == "for_":
                v1_start, v1_stop, v1_step = v1.sweep
                with qua.for_(v1.var, v1_start, v1.var < v1_stop, v1.var + v1_step):
                    qua_function()
            if v1.sweep_type == "for_each_":
                with qua.for_each_(v1.var, v1.sweep):
                    qua_function()

        # If only v2 sweep is configured
        elif v1.sweep is None:
            if v2.sweep_type == "for_":
                v2_start, v2_stop, v2_step = v2.sweep
                with qua.for_(v2.var, v2_start, v2.var < v2_stop, v2.var + v2_step):
                    qua_function()
            if v2.sweep_type == "for_each_":
                with qua.for_each_(v2.var, v2.sweep):
                    qua_function()

        # If both v1 and v2 sweeps are configured, branch according to the sweep types

        elif v1.sweep_type == "for_" and v2.sweep_type == "for_":
            with qua.for_(v1.var, v1_start, v1.var < v1_stop, v1.var + v1_step):
                with qua.for_(v2.var, v2_start, v2.var < v2_stop, v2.var + v2_step):
                    qua_function()

        elif v1.sweep_type == "for_" and v2.sweep_type == "for_each_":
            with qua.for_(v1.var, v1_start, v1.var < v1_stop, v1.var + v1_step):
                with qua.for_each_(v2.var, v2.sweep):
                    qua_function()

        elif v1.sweep_type == "for_" and v2.sweep_type == "for_each_":
            with qua.for_each_(v1.var, v1.sweep):
                with qua.for_(v2.var, v2_start, v2.var < v2_stop, v2.var + v2_step):
                    qua_function()

        elif v1.sweep_type == "for_" and v2.sweep_type == "for_each_":
            with qua.for_each_(v1.var, v1.sweep):
                with qua.for_each_(v2.var, v2.sweep):
                    qua_function()


def Char_1D_singledisplacement(
    cav,
    qubit,
    displacement_pulse,
    qubit_pi_pulse,
    qubit_pi2_pulse,
    ampx,
    delay,
    measure_real,
    tomo_phase,
    correction_phase=0,
):

    # bring qubit into superposition
    qua.align(qubit.name, cav.name)

    qubit.play(
        qubit_pi2_pulse,
    )

    # start ECD gate
    qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
    # First positive displacement
    cav.play(displacement_pulse, ampx, phase=tomo_phase)

    qua.wait(int(delay // 4), cav.name)
    # First negative displacement
    cav.play(displacement_pulse, -ampx, phase=tomo_phase)

    qua.align(qubit.name, cav.name)
    qubit.play(qubit_pi_pulse, phase=0.0)  # play pi to flip qubit around X
    qua.align(cav.name, qubit.name)  # wait for qubit pulse to end

    # Second negative displacement
    cav.play(displacement_pulse, -ampx, phase=tomo_phase)

    qua.wait(int(delay // 4), cav.name)
    # Second positive displacement
    cav.play(displacement_pulse, ampx, phase=tomo_phase)
    qua.align(qubit.name, cav.name)

    qubit.play(
        qubit_pi2_pulse,
        phase=correction_phase + (0 if measure_real else 0.25),
    )  # play pi/2 pulse around X or SY, to measure either the real or imaginary part of the characteristic function
    # qubit.play(qubit_pi2_pulse, phase=measure_real)  # 0 else 0.25  # play


def Char_2D_singledisplacement(
    cav,
    qubit,
    displacement_pulse,
    qubit_pi_pulse,
    qubit_pi2_pulse,
    ampx_x,
    ampx_y,
    delay,
    measure_real,
    tomo_phase,
    correction_phase=0,
):

    # bring qubit into superposition
    qua.align(qubit.name, cav.name)
    qubit.play(qubit_pi2_pulse)

    # start ECD gate
    qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
    # First positive displacement
    cav.play(
        displacement_pulse, ampx=(ampx_x, -ampx_y, ampx_y, ampx_x), phase=tomo_phase
    )

    qua.wait(int(delay // 4), cav.name)
    # First negative displacement
    cav.play(
        displacement_pulse, ampx=(-ampx_x, ampx_y, -ampx_y, -ampx_x), phase=tomo_phase
    )

    qua.align(qubit.name, cav.name)
    qubit.play(qubit_pi_pulse, phase=0.0)  # was 0.25  play pi to flip qubit around X
    qua.align(cav.name, qubit.name)  # wait for qubit pulse to end

    # Second negative displacement
    cav.play(
        displacement_pulse, ampx=(-ampx_x, ampx_y, -ampx_y, -ampx_x), phase=tomo_phase
    )

    qua.wait(int(delay // 4), cav.name)
    # Second positive displacement
    cav.play(
        displacement_pulse, ampx=(ampx_x, -ampx_y, ampx_y, ampx_x), phase=tomo_phase
    )
    # cav.play(
    #     displacement_pulse,
    #     ampx=(c * ampx_x, -c * ampx_y, c * ampx_y, c * ampx_x),
    #     phase=tomo_phase,
    # )

    qua.align(qubit.name, cav.name)

    qubit.play(
        qubit_pi2_pulse, phase=correction_phase + (0 if measure_real else 0.25)
    )  # play pi/2 pulse around X or SY, to measure either the real or imaginary part of the characteristic function


def ECD(
    cav, qubit, displacement_pulse, qubit_pi_pulse, ampx, delay, tomo_phase, qubit_phase
):
    qua.align()  # wait for qubit pulse to end
    # start ECD gate
    qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
    # First positive displacement
    cav.play(displacement_pulse, ampx, phase=tomo_phase)

    qua.wait(int(delay // 4), cav.name)
    # First negative displacement
    cav.play(displacement_pulse, -ampx, phase=tomo_phase)

    qua.align(qubit.name, cav.name)
    qubit.play(qubit_pi_pulse, phase=qubit_phase)  # play pi to flip qubit around X
    qua.align(cav.name, qubit.name)  # wait for qubit pulse to end

    # Second negative displacement
    cav.play(displacement_pulse, -ampx, phase=tomo_phase)

    qua.wait(int(delay // 4), cav.name)
    # Second positive displacement
    cav.play(displacement_pulse, ampx, phase=tomo_phase)
    qua.align(qubit.name, cav.name)
    qua.align()


def U(cav, qubit, displacement_pulse, qubit_pi_pulse, qubit_pi2_pulse, ampx, delay):
    qua.align()
    qubit.play(qubit_pi2_pulse, phase=0.5)

    ECD(
        cav,
        qubit,
        displacement_pulse,
        qubit_pi_pulse,
        ampx,
        delay,
        phase=0,
        qubit_phase=0,
    )

    # qubit.play(qubit_pi_pulse, phase=0.75)  #0.25 in ECD and 0.75 to flip back
    # qubit.play(qubit_pi2_pulse, phase=0)

    qubit.play(qubit_pi2_pulse, phase=0.5)
    qua.align()


def V(cav, qubit, displacement_pulse, qubit_pi_pulse, qubit_pi2_pulse, ampx, delay):
    qua.align()
    qubit.play(qubit_pi2_pulse, phase=0.25)

    ECD(
        cav,
        qubit,
        displacement_pulse,
        qubit_pi_pulse,
        ampx,
        delay,
        phase=0.25,
        qubit_phase=0.25,
    )

    # qubit.play(qubit_pi_pulse, phase=0.75)  # reverse pi flip in ECD
    # qubit.play(qubit_pi2_pulse, phase=0.75)
    qubit.play(qubit_pi2_pulse, phase=0.25)  # reverse pi flip in ECD
    qua.align()
