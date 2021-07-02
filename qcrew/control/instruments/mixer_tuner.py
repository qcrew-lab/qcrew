""" """

from qm.qua import infinite_loop_, play, program  # TODO
from qm.QuantumMachine import QuantumMachine  # TODO

from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.modes.mode import Mode
from qcrew.helpers import logger


class MixerTuner:
    """ """

    def __init__(self, sa: Sa124, qm: QuantumMachine, *modes: Mode) -> None:
        """ """
        self._sa: Sa124 = sa
        self._qm: QuantumMachine = qm
        self._modes: tuple[Mode] = modes
        logger.info(f"Call `.tune()` to tune mixers of {self._modes}")

    def _get_qua_program(self, mode: Mode):  # -> ? TODO
        """ """
        with program() as mixer_tuning:
            with infinite_loop_():
                mode.play_constant_pulse()
        return mixer_tuning

    def tune(self) -> None:
        """ """
        try:
            for mode in self._modes:
                mode.lo_freq = mode.lo_freq  # play carrier freq to mode
                job = self._qm.execute(self._get_qua_program(mode))  # play int freq
                # get bool to tune LO and/or SB
                # tune LO if needs tuning
                # tune SB if needs tuning
        except AttributeError as e:
            logger.error("")
            raise SystemExit() from e
        else:
            # log msg
            job.halt()
