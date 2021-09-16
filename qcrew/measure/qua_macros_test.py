from google.protobuf.struct_pb2 import Value
import numpy as np
import copy
from numpy.core.fromnumeric import var
from qm import qua
from qcrew.helpers.parametrizer_test import Parametrized
from typing import Union, Optional, List, Tuple, Callable

QUA_VAR = Union[int, bool, qua.fixed]
VAL_VAR = Union[int, float, bool]


class Variable(Parametrized):
    def __init__(self, name: str, **kwargs):
        self.name = name

        parametrized_dict = copy.deepcopy(self.__dict__)
        parametrized_dict.update(kwargs)

        super().__init__(**parametrized_dict)



class ExpVariable(Variable):
    def __init__(self,
                 name:str,
                 var_type:QUA_VAR,
                 value:Optional[Union[List[VAL_VAR], VAL_VAR]]=None,
                 size:Optional[int]=None,
                 **kwargs):

        self.var_type = var_type

        if value and not size:
            self.value = value
        if size and not value:
            self.size = size
        if value:
            self.length = len(value)

        super().__init__(name=name, **kwargs)

    def declare(self):
        return qua.declare(self.var_type, value=self.value, size=self.size)


class SweepVariable(ExpVariable):
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
        if sweep:
            self.start = sweep[0]
            self.stop = sweep[1]
            self.step = sweep[2]
            self.length = len(
                np.arange(self.start, self.stop + self.step / 2, self.step)
            )
            self.sweep_type = "for_"
        elif start and stop and step:
            self.start = start
            self.stop = stop
            self.step = step
            self.length = len(
                np.arange(self.start, self.stop + self.step / 2, self.step)
            )
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

        self.name = (name,)
        self.average = average
        self.timestamps = timestamps
        self.save_all = save_all
        self.save = save
        self.buffer_shape = buffer_shape

        super().__init__(name=name, **kwargs)


def IQ_results(
    I_stream,
    Q_stream,
    buffer_shape: Optional[tuple] = None,
    tag: List[str] = ["I", "Q"],
) -> list:
    i = tag[0]
    q = tag[1]

    if buffer_shape:
        I_raw = I_stream.buffer(buffer_shape)
        Q_raw = Q_stream.buffer(buffer_shape)
    else:
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
    adc_stream, input: int = 1, buffer_shape: Optional[tuple] = None, tag: str = "ADC"
) -> list:

    if buffer_shape:
        adc1 = adc_stream.input1().buffer(buffer_shape)
        adc2 = adc_stream.input2().buffer(buffer_shape)
    else:
        adc1 = adc_stream.input1()
        adc2 = adc_stream.input2()

    if input == 1:
        adc1.timestamps().save_all(f"{tag}_TIMESTAMPS")
        adc1.save_all(f"{tag}_RAW")
    elif input == 2:
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

    if buffer_shape:
        state = state_stream.buffer(buffer_shape)
    else:
        state = state_stream

    state.save_all(f"{tag}")
    result_var_list = []
    result_var_list.append(
        ResultVariable(
            f"{tag}", buffer_shape=buffer_shape, average=False, save_all=True
        )
    )

    return result_var_list


def Z_results(
    I_stream, Q_stream, buffer_shape: Optional[tuple], tag: str = "Z_SQ"
) -> list:

    # Z = I^2 + Q^2
    if buffer_shape:
        I_raw = I_stream.buffer(buffer_shape)
        Q_raw = Q_stream.buffer(buffer_shape)
    else:
        I_raw = I_stream
        Q_raw = Q_stream

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
    qua_funciton: Callable,
    sweep_variables: List[SweepVariable],
    declared_variables: list,
) -> None:

    if len(sweep_variables) == len(declared_variables) and len(sweep_variables) != 0:
        for index, var in enumerate(sweep_variables):
            if var.value is None and var.start is not None:
                swept_var = declared_variables[index]
                with qua.for_(
                    swept_var,
                    var.start,
                    swept_var < var.stop + var.step / 2,
                    swept_var + var.step,
                ):
                    del sweep_variables[0]
                    del declared_variables[0]
                    qua_loop(qua_funciton, sweep_variables, declared_variables)
            elif var.value is not None:
                swept_var = declared_variables[index]
                with qua.for_each_(swept_var, var.value):
                    del sweep_variables[0]
                    del declared_variables[0]
                    qua_loop(qua_funciton, sweep_variables, declared_variables)

    else:
        qua_funciton()


def qua_var_declare(
    variables: List[Union[ExpVariable, StreamVariable, SweepVariable]]
) -> list:

    var_list = []
    for var in variables:
        globals()[var.name] = var.declare()
        var_list.append(globals()[var.name])
    return var_list


if __name__ == "__main__":
    sweep_test = SweepVariable(name="a", var_type=qua.fixed, sweep=(0, 5, 1))
