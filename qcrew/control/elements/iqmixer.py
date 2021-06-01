""" """
from dataclasses import asdict, dataclass, field
from typing import ClassVar

from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Paramable


@dataclass(repr=False, eq=False)
class IQMixerOffsets:
    """ """

    keyset: ClassVar[tuple[str]] = ("I", "Q", "G", "P")

    # pylint: disable=invalid-name
    # these names have specific meanings that are well understood by qcrew

    # DC offset applied by a OPX AO port to the I port of the IQMixer
    I: float = field(default=0.0)
    # DC offset applied by a OPX AO port to the Q port of the IQMixer
    Q: float = field(default=0.0)
    # offset used by OPX to correct the gain imbalance of the IQMixer
    G: float = field(default=0.0)
    # offset used by OPX to correct the phase imbalance of the IQMixer
    P: float = field(default=0.0)

    # pylint: enable=invalid-name


class IQMixer(Paramable):
    """ """

    _parameters: ClassVar[set[str]] = {"offsets"}

    def __init__(self, name: str, offsets: dict[str, float] = None) -> None:
        self._name = str(name)
        self._offsets: IQMixerOffsets = IQMixerOffsets()  # initialize default offsets
        if offsets is not None:
            self.offsets = offsets  # set offsets if specified by user

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}, offsets: {self.offsets}"

    @property  # name getter
    def name(self) -> str:
        """ """
        return self._name

    @property  # offsets getter
    def offsets(self) -> dict[str, float]:
        """ """
        return asdict(self._offsets)

    @offsets.setter
    def offsets(self, new_offsets: dict[str, float]) -> None:
        """ """
        valid_keys = IQMixerOffsets.keyset
        try:
            for key, value in new_offsets.items():
                if key in valid_keys:
                    setattr(self._offsets, key, value)
                    logger.success(f"Set {self._name} {key} offset to {value}")
                else:
                    logger.warning(f"Ignored invalid offset {key = }, {valid_keys = }")
        except AttributeError:
            logger.exception(f"Setter expects {dict[str, float]} with {valid_keys = }")
