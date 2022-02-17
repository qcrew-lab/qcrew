""" """

from typing import ClassVar

from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers.yamlizer import Yamlizable
from pathlib import Path
import numpy as np


class ConstantIntegrationWeights(Parametrized, Yamlizable):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "magnitude", "is_pinned"}
    keys: ClassVar[tuple[str]] = ("iw_i", "iw_q")

    def __init__(
        self,
        length: int = None,  # length of demodulation window divided by 4, in ns
        magnitude: tuple[float] = (1.0, 0.0, 0.0, 1.0),  # (i_cos, i_sin, q_cos, q_sin)
        is_pinned: bool = True,  # if true, demodulation window == readout pulse length
    ) -> None:
        """[summary]

        Args:
            length (int, optional): [description]. Defaults to None.
            innsmagnitude (tuple[float], optional): [description]. Defaults to (1.0, 0.0, 0.0, 1.0).
            demodulationwindow ([type], optional): [description]. Defaults to =readoutpulselength.
        """
        self.length = length
        self.magnitude = magnitude
        self.is_pinned = is_pinned

    @property  # integration weights samples getter
    def samples(self) -> dict[str, dict[str, list]]:
        """ """
        samples = [[value] * self.length for value in self.magnitude]
        return {
            self.keys[0]: {"cosine": samples[0], "sine": samples[1]},
            self.keys[1]: {"cosine": samples[2], "sine": samples[3]},
        }


class OptimizedIntegrationWeights(Parametrized, Yamlizable):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "path", "weights"}
    keys: ClassVar[tuple[str]] = ("iw_i", "iw_q")

    def __init__(
        self,
        length: int = None,  # length of demodulation window divided by 4, in ns
        path: str = None,
        is_pinned: bool = True,
    ) -> None:

        self.length = length
        self.path = path
        self.weights = None
        self.is_pinned = is_pinned
        if self.path is not None:
            self.weights = np.load(Path(self.path))
            self.length = len(self.weights["I"][0])

    def __call__(self, path) -> None:
        self.path = str(path)

        self.weights = np.load(Path(self.path))
        self.length = len(self.weights["I"][0])

    @property  # integration weights samples getter
    def samples(self) -> dict[str, dict[str, list]]:
        """ """
        if self.weights is not None:
            return {
                self.keys[0]: {
                    "cosine": self.weights["I"][0],
                    "sine": self.weights["Q"][0],
                    # "sine": np.zeros(len(self.weights["I"][0])),
                },
                self.keys[1]: {
                    "cosine": self.weights["I"][1],
                    # "cosine": np.zeros(len(self.weights["I"][0])),
                    "sine": self.weights["Q"][1],
                },
            }
        else:
            samples = [[value] * self.length for value in (1.0, 0.0, 0.0, 1.0)]
            return {
                self.keys[0]: {"cosine": samples[0], "sine": samples[1]},
                self.keys[1]: {"cosine": samples[2], "sine": samples[3]},
            }
