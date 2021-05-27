""" """
from dataclasses import asdict, dataclass, field
from typing import ClassVar

from qcrew.helpers import logger
from qcrew.instruments.instrument import Instrument


@dataclass(repr=False, eq=False)
class IQMixerOffsets:
    """ """

    # class variable defining the keyset of the offsets of IQMixer objects
    keyset: ClassVar[frozenset[str]] = frozenset(["I", "Q", "G", "P"])

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


class IQMixer(Instrument):
    """ """

    # class variable defining the parameter set for IQMixer objects
    _parameters: ClassVar[set[str]] = set(["offsets"])

    def __init__(self, name: str, offsets: dict[str, float] = None) -> None:
        self._name = str(name)
        self._offsets: IQMixerOffsets = self._create_offsets(offsets)  # settable

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}, offsets: {self.offsets}"

    def _create_offsets(self, offsets: dict[str, float]) -> IQMixerOffsets:
        """ """
        valid_keys = IQMixerOffsets.keyset
        if not isinstance(offsets, dict) or not offsets:
            logger.warning(f"No {self._name} offsets given, setting default values...")
            return IQMixerOffsets()
        elif set(offsets) == valid_keys:  # got all valid offsets
            return IQMixerOffsets(**offsets)
        elif set(offsets) < valid_keys:  # got some valid offsets
            logger.warning(f"Setting defaults for unspecified {self._name} offsets...")
            return IQMixerOffsets(**offsets)
        else:  # got partially valid offsets dict
            logger.warning(f"Ignoring invalid {self._name} offset(s) keys...")
            valid_offsets = {k: offsets[k] for k in valid_keys if k in offsets}
            return IQMixerOffsets(**valid_offsets)

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
        valid_keys = set(IQMixerOffsets.keyset)
        try:
            for key, value in new_offsets.items():
                if key in valid_keys:
                    setattr(self._offsets, key, value)
                    logger.success(f"Set {self._name} {key} offset to {value}")
                else:
                    logger.warning(f"Ignored invalid offset {key = }, {valid_keys = }")
        except AttributeError:
            logger.exception(f"Setter expects {dict[str, float]} with {valid_keys = }")
