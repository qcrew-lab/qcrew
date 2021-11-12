import numpy as np
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from copy import deepcopy
import matplotlib.pyplot as plt


class TimeDiffCalibrator:
    def __init__(
        self,
        qmm,
        config,
        qe,
        int_freq=None,
        pulse_length=None,
        reps=None,
        analog_input=None,
    ) -> None:

        self.qmm = qmm
        if qe in config["elements"]:

            self.qe = qe
            self.old_int_freq = config["elements"][self.qe]["intermediate_frequency"]
            self.int_freq = int_freq or -1e6

            self.pulse_length = pulse_length or 2000

            self.reps = reps or 100

            self.config = self._update_config(
                int_freq=self.int_freq,
                config=config,
                qe=self.qe,
                pulse_length=self.pulse_length,
            )

            self.analog_input = analog_input or "out1"

            self.time_of_flight = self.config["elements"][self.qe]["time_of_flight"]
            self.smearing = self.config["elements"][self.qe]["smearing"]
            self.i_port = self.config["elements"][self.qe]["mixInputs"]["I"]
            self.q_port = self.config["elements"][self.qe]["mixInputs"]["Q"]
            self.analog_input_port = self.config["elements"][self.qe]["outputs"][
                self.analog_input
            ]

        else:
            raise ValueError(
                "The element " + qe + "does not exit in the configuration."
            )

    @staticmethod
    def _update_config(int_freq, config, qe, pulse_length):
        config = deepcopy(config)
        config["elements"][qe]["operations"][
            "time_diff_long_readout"
        ] = "time_diff_long_readout_pulse"
        config["elements"][qe]["intermediate_frequency"] = int_freq
        config["mixers"][config["elements"][qe]["mixInputs"]["mixer"]][0][
            "intermediate_frequency"
        ] = int_freq
        config["pulses"]["time_diff_long_readout_pulse"] = {
            "operation": "measurement",
            "length": int(pulse_length),
            "waveforms": {
                "I": "time_diff_const_wf",
                "Q": "time_diff_zero_wf",
            },
            "integration_weights": {
                "time_diff_integW1": "time_diff_integW1",
                "time_diff_integW2": "time_diff_integW2",
            },
            "digital_marker": "time_diff_ON",
        }
        config["digital_waveforms"]["time_diff_ON"] = {"samples": [(1, 0)]}
        config["waveforms"]["time_diff_const_wf"] = {"type": "constant", "sample": 0.2}
        config["waveforms"]["time_diff_zero_wf"] = {"type": "constant", "sample": 0.0}
        config["integration_weights"]["time_diff_integW1"] = {
            "cosine": [1.0] * int(pulse_length / 4),
            "sine": [0.0] * int(pulse_length / 4),
        }

        config["integration_weights"]["time_diff_integW2"] = {
            "cosine": [0.0] * int(pulse_length / 4),
            "sine": [1.0] * int(pulse_length / 4),
        }
        return config

    @staticmethod
    def qua_program(reps, qe, analog_input):

        if analog_input == "out1" or analog_input == "out2":
            with program() as cal_phase:
                I = declare(fixed)
                Q = declare(fixed)
                n = declare(int)
                adc = declare_stream(adc_trace=True)

                with for_(n, 1, n < reps + 1 / 2, n + 1):
                    # reset_phase(qe)
                    measure(
                        "time_diff_long_readout",
                        qe,
                        adc,
                        demod.full("time_diff_integW1", I, analog_input),
                        demod.full("time_diff_integW2", Q, analog_input),
                    )
                    save(I, "I")
                    save(Q, "Q")

                with stream_processing():
                    if analog_input == "out1":
                        adc.input1().timestamps().save_all("timestamps")
                        adc.input1().save_all("adc")
                    elif analog_input == "out2":
                        adc.input1().timestamps().save_all("timestamps")
                        adc.input1().save_all("adc")
            return cal_phase

        elif analog_input == "out1out2":
            with program() as cal_phase:
                I1 = declare(fixed)
                Q1 = declare(fixed)
                I2 = declare(fixed)
                Q2 = declare(fixed)
                I = declare(fixed)
                Q = declare(fixed)
                n = declare(int)
                adc_st = declare_stream(adc_trace=True)

                with for_(n, 1, n < reps + 1, n + 1):
                    # reset_phase(qe)
                    measure(
                        "time_diff_long_readout",
                        qe,
                        adc_st,
                        demod.full("time_diff_integW1", I1, "out1"),
                        demod.full("time_diff_integW2", Q1, "out1"),
                        demod.full("time_diff_integW1", I2, "out2"),
                        demod.full("time_diff_integW2", Q2, "out2"),
                    )
                    assign(I, I1 + Q2)
                    assign(Q, -Q1 + I2)
                    save(I, "I")
                    save(Q, "Q")

                with stream_processing():
                    adc_st.input1().with_timestamps().save_all("adc1")
                    adc_st.input2().with_timestamps().save_all("adc2")
                    adc_st.input1().timestamps().save_all("timestamps1")
                    adc_st.input2().timestamps().save_all("timestamps2")

            return cal_phase
        else:
            raise ValueError("analog_input must be either 1 or 2")

    def calibrate(self, simulate=False, **execute_args) -> None:
        """The intermediate frequency is set a magic value around 1e6~5e6 with which the time difference between the IF signal sent to the
        path of modualtion and that sent to the demodulation process.
        """
        cal_phase = self.qua_program(
            reps=self.reps, qe=self.qe, analog_input=self.analog_input
        )
        qm = self.qmm.open_qm(self.config)

        if not simulate:
            job = qm.execute(cal_phase, **execute_args)
        else:
            redundancy = 1000
            time = self.reps * (self.time_of_flight + 2 * self.smearing + redundancy)
            simulation_config = SimulationConfig(
                duration=time,
                simulation_interface=LoopbackInterface(
                    [
                        (
                            self.i_port[0],
                            self.i_port[1],
                            self.analog_input_port[0],
                            self.analog_input_port[1],
                        ),
                        (
                            self.q_port[0],
                            self.q_port[1],
                            self.analog_input_port[0],
                            self.analog_input_port[1],
                        ),
                    ],
                    latency=self.time_of_flight,
                    noisePower=0.07 ** 2,
                ),
            )
            # self.q_port[0], self.q_port[1], self.analog_input_port[0], self.analog_input_port[1]
            # [("con1", 1, "con1", 1) ("con1", 2, "con1", 1)] simualte the I and Q signals are mixed by IQ mixer,
            # downcoverted by IR mixer, then sent to the analog input 1
            # [("con1", 1, "con1", 1) ("con1", 2, "con1", 2)] simualte the I and Q signals are mixed by IQ mixer,
            # downcoverted by IQ mixer, then the I Q signal are sent to the analog input 1 and 2 respectively.
            job = self.qmm.simulate(self.config, cal_phase, simulation_config)

        res = job.result_handles
        res.wait_for_all_values()

        adc = res.get("adc").fetch_all()["value"]
        timestamps = res.get("timestamps").fetch_all()["value"]

        # adc_ts = timestamps - timestamps[0]
        adc_ts = timestamps[0]
        adc_avg = np.mean(adc, axis=0)

        plt.figure()
        plt.plot(adc_ts, adc_avg)
        plt.show()

        I = res.get("I").fetch_all()["value"]
        Q = res.get("Q").fetch_all()["value"]
        I_avg = np.mean(I, axis=0)
        Q_avg = np.mean(Q, axis=0)

        if self.smearing != 0:
            adc_avg_demod = adc_avg[self.smearing : -self.smearing]
            adc_ts_demod = adc_ts[self.smearing : -self.smearing]
        else:
            adc_avg_demod = adc_avg
            adc_ts_demod = adc_ts

        # adc_avg_demod = adc_avg
        # adc_ts_demod = adc_ts
        sig_cos = adc_avg_demod * np.cos(
            2 * np.pi * self.int_freq * 1e-9 * adc_ts_demod
        )

        # TODO: check the sign
        sig_sin = adc_avg_demod * np.sin(
            2 * np.pi * self.int_freq * 1e-9 * adc_ts_demod
        )

        I_ = np.sum(sig_cos)
        Q_ = np.sum(sig_sin)

        time_diff_ns = (
            np.angle((I_avg + 1j * Q_avg) / (I_ + 1j * Q_))
            / 1e-9
            / 2
            / np.pi
            / np.abs(self.int_freq)
        )
        time_diff = np.round(time_diff_ns / 4) * 4

        print("demod adc length", np.shape(adc_ts_demod))
        print("adc raw length", np.shape(adc_ts))
        print("I:", I_avg)
        print("Q:", Q_avg)
        print("I_:", I_)
        print("Q_:", Q_)
        print("angle:", np.angle((I_avg + 1j * Q_avg) / (I_ + 1j * Q_)))

        print("time_diff_ns:", time_diff_ns)
        print("time_diff:", time_diff)

        return time_diff
