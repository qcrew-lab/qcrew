import qcrew.helpers.yamlizer as yml

class TestLabBrick(yml.Yamlizable):

    _parameters = {"frequency"}

    def __init__(self, id, frequency):
        self._id = id
        self._frequency = None
        self.frequency = frequency

    @property
    def id(self):
        return self._id

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, new_frequency):
        self._frequency = new_frequency

    def __repr__(self) -> str:
        return f"TLB{self.id}"

    def disconnect(self):
        pass
