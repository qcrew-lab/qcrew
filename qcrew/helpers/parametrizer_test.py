from collections.abc import MutableMapping
import yaml

class Parametrized(MutableMapping):
    
    _parameter = dict()
    def __init__(self, *args, **kwargs):
        for item in args:
            if isinstance(item, str):
                self.update({item: None})
            elif (
                isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)
            ):
                self.update({item[0]: item[1]})
            else:
                raise ValueError(
                    "The arguments given in *args have wrong format. Correct argument format:[str] or ([str], [other type])"
                )

        self.update(kwargs)  # use the free update to set keys
    
    @property
    def parameter(self):
        return self._parameter

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

    def __str__(self):
       return yaml.dump(self._parameter, sort_keys=False, default_style=False)

    @property
    def parameters(self):
        return self._parameter
    

if __name__ == "__main__":
    test = Parametrized(
        "key1", "key2", ("name", "test_name"), ("length", 21), arg3=3, arg4=4
    )
    print(test)
