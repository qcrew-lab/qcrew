import qcrew.helpers.yamlizer as yml

class TestMode(yml.Yamlizable):

    _parameters = {"lo_freq", "int_freq", "ports"}

    def __init__(self, name, lo, int_freq, ports, lo_freq = None):
        self.name = name
        self.lo = lo
        self.int_freq = int_freq
        self.ports = ports

        if lo_freq is not None:
            self.lo_freq = lo_freq

    @property
    def lo_freq(self):
        return self.lo.frequency

    @lo_freq.setter
    def lo_freq(self, new_lo_freq):
        self.lo.frequency = new_lo_freq

    def __repr__(self):
        """ """
        return f"{type(self).__name__} '{self.name}'"

    @property
    def parameters(self):
        return {name: getattr(self, name) for name in self._parameters}


class TestReadoutMode(TestMode):

    _parameters = TestMode._parameters | {"tof"}

    def __init__(self, tof, **parameters) -> None:
        """ """
        super().__init__(**parameters)
        self.tof: int = tof
