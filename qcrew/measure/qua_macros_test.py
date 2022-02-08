"""This module contains the classes that pack the QUA variables and statements
"""
import numpy as np
from qm import qua
from qcrew.helpers.parametrizer_test import Parametrized
from typing import Union, Optional, List, Callable

QUA_VAR = Union[int, bool, qua.fixed]
VAL_VAR = Union[int, float, bool]


class Variable(Parametrized):
    """[summary]

    Args:
        Parametrized ([type]): [description]
    """

    def __init__(self, name: str, **kwargs):
        self.name = name

        super().__init__(**kwargs)


class ExpVariable(Variable):
    """[summary]

    Args:
        Variable ([type]): [description]
    """

    def __init__(
        self,
        name: str,
        var_type: QUA_VAR,
        value: Optional[Union[List[VAL_VAR], VAL_VAR]] = None,
        size: Optional[int] = None,
        **kwargs,
    ):

        self.var_type = var_type
        self.value = value
        self.size = size
        if value:
            self.length = len(value)

        super().__init__(name=name, **kwargs)

    def declare(self):
        return qua.declare(self.var_type, value=self.value, size=self.size)


class SweepVariable(ExpVariable):
    """[summary]

    Args:
        ExpVariable ([type]): [description]
    """

    def __init__(
        self,
        name: str,
        var_type: QUA_VAR,
        value: Optional[Union[List[VAL_VAR], VAL_VAR]] = None,
        size: Optional[int] = None,
        sweep: Optional[tuple] = None,
        start: Optional[VAL_VAR] = None,
        stop: Optional[VAL_VAR] = None,
        step: Optional[VAL_VAR] = None,
        **kwargs,
    ):

        # TODO: type check
        if value:
            self.sweep_type = "for_each_"
            self.length = len(value)
        elif sweep:
            if var_type == int:
                self.start = int(sweep[0])
                self.stop = int(sweep[1])
                self.step = int(sweep[2])
            elif var_type == qua.fixed:
                self.start = float(sweep[0])
                self.stop = float(sweep[1])
                self.step = float(sweep[2])

            self.length = len(np.arange(self.start, self.stop, self.step))
            self.sweep_type = "for_"
        elif start and stop and step:
            if var_type == int:
                self.start = int(start)
                self.stop = int(stop)
                self.step = int(step)
            elif var_type == qua.fixed:
                self.start = float(start)
                self.stop = float(stop)
                self.step = float(step)

            self.length = len(np.arange(self.start, self.stop, self.step))
            self.sweep_type = "for_"

        super().__init__(name=name, var_type=var_type, value=value, size=size, **kwargs)

    @property
    def sample(self):
        if "value" in self.__dict__.keys():
            return np.array(self.value)
        elif "start" in self.__dict__.keys():
            return np.arange(self.start, self.stop + self.step / 2, self.step)
        else:
            raise ValueError("The sweep variable is not well defined.")


class StreamVariable(Variable):
    def __init__(self, name: str, adc_trace: bool = False, **kwargs):
        self.adc_trace = adc_trace

        super().__init__(name=name, **kwargs)

    def declare(self):
        return qua.declare_stream(adc_trac=self.adc_trace)


class ResultVariable(Variable):
    """[summary]

    Args:
        Variable ([type]): [description]
    """

    def __init__(
        self,
        name: str,
        buffer_shape: Optional[tuple] = None,
        average: bool = True,
        timestamps: bool = False,
        save_all: bool = True,
        save: bool = False,
        **kwargs,
    ):

        self.name = name
        self.average = average
        self.timestamps = timestamps
        self.save_all = save_all
        self.save = save
        self.buffer_shape = buffer_shape

        super().__init__(name=name, **kwargs)


def sweep_results(var_stream, tag: str, buffer_shape: Optional[tuple] = None):

    if buffer_shape:
        for length in buffer_shape:
            var_stream = var_stream.buffer(length)

    var_stream.save(tag)


def IQ_results(
    I_stream,
    Q_stream,
    buffer_shape: Optional[tuple] = None,
    tag: Optional[list[str]] = None,
) -> list:
    if tag:
        i, q = tag[0], tag[1]
    else:
        i, q = "I", "Q"

    if buffer_shape:
        for length in buffer_shape:
            I_stream = I_stream.buffer(length)
            Q_stream = Q_stream.buffer(length)

    I_raw = I_stream
    Q_raw = Q_stream

    I_raw.save_all(f"{i}_RAW")
    Q_raw.save_all(f"{q}_RAW")

    I_raw.average().save_all(f"{i}_RAW_AVG")
    Q_raw.average().save_all(f"{q}_RAW_AVG")

    I_raw.average().save(f"{i}_AVG")
    Q_raw.average().save(f"{q}_AVG")

    result_var_list = []
    result_var_list.append(
        ResultVariable(
            f"{i}_RAW", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(
            f"{q}_RAW", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(
            f"{i}_RAW_AVG", buffer_shape=buffer_shape, average=True, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(
            f"{q}_RAW_AVG", buffer_shape=buffer_shape, average=True, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(f"{i}_AVG", buffer_shape=buffer_shape, average=True, save=True)
    )
    result_var_list.append(
        ResultVariable(f"{q}_AVG", buffer_shape=buffer_shape, average=True, save=True)
    )

    return result_var_list


def ADC_results(
    adc_stream,
    analog_input: str = "out1",
    buffer_shape: Optional[tuple] = None,
    tag: str = "ADC",
) -> list:

    adc1 = adc_stream.input1()
    adc2 = adc_stream.input2()

    if buffer_shape:
        for length in buffer_shape:
            adc1 = adc1.buffer(length)
            adc2 = adc2.buffer(length)

    if analog_input == "out1":
        adc1.timestamps().save_all(f"{tag}_TIMESTAMPS")
        adc1.save_all(f"{tag}_RAW")
    elif analog_input == "out2":
        adc2.timestamps().save_all(f"{tag}_TIMESTAMPS")
        adc2.save_all(f"{tag}_RAW")

    result_var_list = []
    result_var_list.append(
        ResultVariable(
            f"{tag}_TIMESTAMPS", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(
            f"{tag}_RAW", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )

    return result_var_list


def STATE_results(
    state_stream, buffer_shape: Optional[tuple] = None, tag: str = "STATE"
) -> list:

    state = state_stream
    if buffer_shape:
        for length in buffer_shape:
            state = state.buffer(length)

    state.save_all(f"{tag}")
    result_var_list = []
    result_var_list.append(
        ResultVariable(
            f"{tag}", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )

    return result_var_list


def var_results(var_stream_list: list, var_name_list: list) -> list:
    result_var_list = []
    if len(var_stream_list) == len(var_name_list):
        for index, var_stream, name in enumerate(zip(var_stream_list, var_name_list)):
            var_stream.save(name)
            result_var_list.append(ResultVariable(name, average=False, save=True))
    else:
        raise ValueError(
            "The lengths of var_stream_list and var_name_list do not match"
        )

    return result_var_list


def Z_results(
    I_stream, Q_stream, buffer_shape: Optional[tuple], tag: str = "Z_SQ"
) -> list:

    # Z = I^2 + Q^2
    I_raw = I_stream
    Q_raw = Q_stream

    if buffer_shape:
        for length in buffer_shape:
            I_raw = I_stream.buffer(length)
            Q_raw = Q_stream.buffer(length)

    # we need these two streams to calculate  std err in a single pass
    (I_raw * I_raw + Q_raw * Q_raw).save_all(f"{tag}_RAW")
    (I_raw * I_raw + Q_raw * Q_raw).average().save_all(f"{tag}_RAW_AVG")

    # to live plot latest average
    (I_raw * I_raw + Q_raw * Q_raw).average().save(f"{tag}_AVG")

    result_var_list = []
    result_var_list.append(
        ResultVariable(
            f"{tag}_RAW", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(
            f"{tag}_RAW_AVG", buffer_shape=buffer_shape, average=True, save_all=True
        )
    )
    result_var_list.append(
        ResultVariable(f"{tag}_AVG", buffer_shape=buffer_shape, average=True, save=True)
    )
    return result_var_list


def qua_loop(
    qua_function: Callable,
    qua_var: list,
    qua_sweep_var: list,
    qua_stream_var: list,
    sweep_variables: List[SweepVariable],
) -> None:

    if len(sweep_variables) != 0:

        var = sweep_variables[0]
        index = len(qua_sweep_var) - len(sweep_variables)

        if var.value is None and var.start is not None:
            swept_var = qua_sweep_var[index]

            with qua.for_(
                swept_var,
                var.start,
                swept_var < var.stop + var.step / 2,
                swept_var + var.step,
            ):
                qua_loop(
                    qua_function,
                    qua_var,
                    qua_sweep_var,
                    qua_stream_var,
                    sweep_variables[1:],
                )
                qua.save(swept_var, var.name)
        elif var.value is not None:
            swept_var = qua_sweep_var[index]
            with qua.for_each_(swept_var, var.value):
                qua_loop(
                    qua_function,
                    qua_var,
                    qua_sweep_var,
                    qua_stream_var,
                    sweep_variables[1:],
                )
                qua.save(swept_var, var.name)
    else:
        qua_function(qua_var, qua_sweep_var, qua_stream_var)


def qua_var_declare(
    variables: List[Union[ExpVariable, StreamVariable, SweepVariable]]
) -> list:

    var_list = []
    for var in variables:
        globals()[var.name] = var.declare()
        var_list.append(globals()[var.name])
    return var_list


if __name__ == "__main__":
    var_test = ExpVariable(name="n", var_type=int)
    sweep_test = SweepVariable(name="a", var_type=qua.fixed, sweep=(0, 5, 1))
