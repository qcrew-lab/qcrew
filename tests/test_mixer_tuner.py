import random

class TestMixerTuner:
    def tune(self, *modes):
        for mode in modes:
            mode.offsets = {
                "I": random.uniform(-0.1, 0.1),
                "Q": random.uniform(-0.1, 0.1),
                "G": random.uniform(-0.25, 0.25),
                "P": random.uniform(-0.25, 0.25),
            }
