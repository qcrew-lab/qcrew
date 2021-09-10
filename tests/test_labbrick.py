""" Test LabBrick that imitates the API of the physical instrument driver """

from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlizable
from qcrew.helpers.parametrizer import Parametrized

class TestLabBrick(Parametrized, Yamlizable):

    _parameters = {"frequency", "power", "rf"}

    def __init__(self, id, name, frequency, power):
        self._id = id
        self._name = str(name)
        self._rf = False
        self._frequency = None
        self.frequency = frequency
        self._power = None
        self.power = power
        self.connect()

    def __repr__(self) -> str:
        return f"TestLabBrick-{self._id}"

    def connect(self):
        logger.info(f"Connected to {self}")

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, new_frequency):
        self._frequency = new_frequency
        if not self._rf:
            self._rf = True

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, new_power):
        self._power = new_power

    @property
    def rf(self) -> bool:
        """ """
        return self._rf

    @rf.setter
    def rf(self, toggle: bool):
        """ """
        self._rf = toggle

    def disconnect(self):
        logger.info(f"Disconnected {self}")
