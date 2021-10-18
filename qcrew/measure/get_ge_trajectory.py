 import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np


reps = 100000


def get_qua_program(rr):....
        with program() as test_program:
            n = declare(int)
            Ig = declare(fixed)
            Qg = declare(fixed)
            Ie = declare(fixed)
            Qe = declare(fixed)
            resg = declare(bool)
            rese = declare(bool)


            adcg = declare_stream(adc_trace=True)
            adce = declare_stream(adc_trace=True)

            with for_(n, 0, n < self.N + 1 / 2, n + 1):
                qubit, rr = self.modes  # get the modes
                
                ## measure g
                qua.align(qubit.name, rr.name)  # wait qubit pulse to end
                rr.measure((self.I, self.Q))  # measure qubit state
                qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
                
                ## measure e 
                qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
                qua.align(qubit.name, rr.name)  # wait qubit pulse to end
                rr.measure((self.I, self.Q))  # measure qubit state
                qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset


                wait(self.wait_time, self.resonator)

            with stream_processing():
                if self.analog_input == "out1":
                    adcg.input1().timestamps().save_all("timestamps_g")
                    adce.input1().timestamps().save_all("timestamps_e")
                    adcg.input1().save_all("adc_g")
                    adce.input1().save_all("adc_e")
                elif self.analog_input == "out2":
                    adcg.input2().timestamps().save_all("timestamps_g")
                    adce.input2().timestamps().save_all("timestamps_e")
                    adcg.input2().save_all("adc_g")
                    adce.input2().save_all("adc_e")
            return test_program