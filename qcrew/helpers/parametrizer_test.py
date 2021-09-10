from collections.abc import MutableMapping

class Parametrized(MutableMapping):
    def __init__(self, *args, **kwargs):
        self._parameter = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self._parameter[self._keytransform(key)]

    def __setitem__(self, key, value):
        self._parameter[self._keytransform(key)] = value

    def __delitem__(self, key):
        del self._parameter[self._keytransform(key)]

    def __iter__(self):
        return iter(self._parameter)
    
    def __len__(self):
        return len(self._parameter)

    def _keytransform(self, key):
        return key
    
    @property
    def parameters(self):
        return self._parameter
