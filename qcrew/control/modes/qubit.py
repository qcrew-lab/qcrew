""" """

from typing import ClassVar

import qcrew.control.pulses as qcp
from qcrew.control.modes.mode import Mode
from qcrew.helpers import logger

from qm import qua


class Qubit(Mode):
    """ """

    _parameters: ClassVar[set[str]] = Mode._parameters | {
        "omegas",  # list of qubit transition frequencies [g->e, e->f, f->g, ...]
        "rotation_ampxs",  # dict where key = rotation angle, value = rotation pulse amp
        "t1",
        "t2",
    }

    _rotation_angle_keys: ClassVar[tuple[str]] = ("0", "pi2", "pi")
    _rotation_axis_keys: ClassVar[tuple[str]] = ("X", "Y")

    def __init__(
        self,
        *,
        omegas: list[float] = None,
        rotation_ampxs: dict[str, float] = None,
        t1: float = None,
        t2: float = None,
        **parameters,
    ):
        """ """
        super().__init__(**parameters)

        if "rotation_pulse" not in self._operations:  # add default selective pulse
            self.operations = {"rotation_pulse": qcp.GaussianPulse(sigma=10)}

        self._omegas: list[float] = list()
        if omegas is not None:
            self.omegas = omegas

        self._rotation_ampxs: dict[str, float] = dict()
        if rotation_ampxs is not None:
            self.rotation_ampxs = rotation_ampxs
        else:
            self._rotation_ampxs = {key: 0.0 for key in self._rotation_angle_keys}

        self.t1: float = t1
        self.t2: float = t2

    @property  # omegas getter
    def omegas(self) -> list[float]:
        """ """
        return self._omegas.copy()

    @omegas.setter
    def omegas(self, new_omega: tuple[int, float]) -> None:
        """ """
        try:
            index, omega = new_omega
        except (ValueError, TypeError):
            logger.error(f"Expect sequence (transition index, omega), got {new_omega}")
        else:
            self._omegas.insert(index, omega)
            logger.success(f"Set transition {index = } with {omega = }")

    @property  # rotation ampx dict getter
    def rotation_ampxs(self) -> dict[str, float]:
        """ """
        return self._rotation_ampxs.copy()

    @rotation_ampxs.setter
    def rotation_ampxs(self, new_rotation_ampxs: dict[str, float]) -> None:
        """ """
        valid_keys = self._rotation_angle_keys
        try:
            for key, ampx in new_rotation_ampxs.items():
                if key in valid_keys:
                    self._rotation_ampxs[key] = ampx
                    logger.success(f"Set {self} '{key}' rotation {ampx = }")
                else:
                    logger.warning(f"Ignored invalid key '{key}', {valid_keys = }")
        except (AttributeError, TypeError):
            logger.error(f"Setter expects {dict[str, float]} with {valid_keys = }")
            raise

    def rotate(self, angle: str = "pi", axis: str = "X") -> None:
        """ """
        try:
            ampx = self._rotation_ampxs[angle]
        except KeyError:
            valid_keys = self._rotation_angle_keys
            logger.error(f"Unrecognized rotation {angle = }, {valid_keys = }")
            raise
        else:
            self._rotate(ampx, axis)

    def _rotate(self, ampx: float, axis: str) -> None:
        """ """
        if axis == "X":
            self._rotate_x(ampx)
        elif axis == "Y":
            self._rotate_y(ampx)
        else:
            valid_keys = self._rotation_axis_keys
            logger.error(f"Unrecognized {axis = }, {valid_keys = }")
            raise ValueError("Invalid rotation axis")

    def _rotate_x(self, ampx: float) -> None:
        """ """
        self.play("rotation_pulse", ampx=ampx)

    def _rotate_y(self, ampx: float) -> None:
        """ """
        qua.frame_rotation_2pi(0.25, self.name)
        self.play("rotation_pulse", ampx=ampx)
        qua.frame_rotation_2pi(-0.25, self.name)
