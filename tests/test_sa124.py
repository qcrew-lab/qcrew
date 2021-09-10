""" Test Sa124 that imitates the API of the physical instrument driver """

from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlizable
from qcrew.helpers.parametrizer import Parametrized

class TestSa124(Parametrized, Yamlizable):

    _parameters = {"center", "span", "sweep_length", "rbw", "ref_power"}

    def __init__(self, id, name, center, span, rbw, ref_power):
        self._id = id
        self._name = str(name)
        self.center = center
        self.span = span
        self.rbw = rbw
        self.ref_power = ref_power
        self.sweep_length = int(span / rbw)
        self.connect()

    def __repr__(self) -> str:
        return f"TestSa124-{self._id}"

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    def connect(self):
        logger.info(f"Connected to {self}")

    def sweep(self):
        logger.success(f"Swept {self.sweep_length} points")

    def disconnect(self):
        logger.info(f"Disconnected {self}")
