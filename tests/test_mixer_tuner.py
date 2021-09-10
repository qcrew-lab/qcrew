""" Test MixerTuner that imitates the behaviour of the meta instrument driver """

import random

from qcrew.helpers import logger

class TestMixerTuner:

    def __init__(self, *modes):
        self._modes = modes

    def tune(self):
        for mode in self._modes:
            try:
                mode.mixer_offsets = {
                    "I": random.uniform(-0.1, 0.1),
                    "Q": random.uniform(-0.1, 0.1),
                    "G": random.uniform(-0.25, 0.25),
                    "P": random.uniform(-0.25, 0.25),
                }
            except AttributeError:
                logger.error("MixerTuner must be initialized with Mode objects")
                raise
