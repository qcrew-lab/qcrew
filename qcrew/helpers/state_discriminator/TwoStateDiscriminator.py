from .StateDiscriminator import StateDiscriminator
import numpy as np
import matplotlib.pyplot as plt
from qm.qua import *
from qm import SimulationConfig, LoopbackInterface
from qm.QuantumMachinesManager import QuantumMachinesManager
from typing import Optional
import seaborn as sns


class TwoStateDiscriminator(StateDiscriminator):
    """This class inherts from ``StateDiscriminator`` class and restrict the number of state being 2."""

    def __init__(
        self,
        qmm: QuantumMachinesManager,
        config: dict,
        resonator: Optional[str] = None,
        resonator_pulse: Optional[str] = None,
        qubit: Optional[str] = None,
        qubit_pulse: Optional[str] = None,
        analog_input: Optional[int] = None,
        path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):

        # optimal weight naming
        if metadata and "integw_cos" in metadata:
            self.iw_cos = metadata["integw_cos"]
        else:
            self.iw_cos = "integW_cos"

        if metadata and "integw_sin" in metadata:
            self.iw_sin = metadata["integw_sin"]
        else:
            self.iw_sin = "integW_sin"

        self.opt_iw_cos = "opt_integW_cos"
        self.opt_iw_sin = "opt_integW_sin"

        super().__init__(
            qmm,
            config,
            resonator,
            resonator_pulse,
            qubit,
            qubit_pulse,
            analog_input,
            path,
            metadata,
        )
        self.num_of_states = 2

    def _update_config(self):
        """Update the integration weights in the opened config for the OPX"""
        weights = self.saved_data["weights"]

        b_vec = weights[0, :] - weights[1, :]
        self.config["integration_weights"][self.opt_iw_cos] = {
            "cosine": np.real(b_vec).tolist(),
            "sine": (np.imag(b_vec)).tolist(),
        }
        self._add_iw_to_all_pulses(self.opt_iw_sin)

        # TODO: check the sign of cosine
        self.config["integration_weights"][self.opt_iw_sin] = {
            "cosine": (-np.imag(b_vec)).tolist(),
            "sine": np.real(b_vec).tolist(),
        }
        self._add_iw_to_all_pulses(self.opt_iw_sin)

    def _simulation_config(self):
        """Provide the simulation config when we perform the simualtion."""
        redundancy = 1000
        time = self.N * (self.time_of_flight + 2 * self.smearing + redundancy)
        simulation_config = SimulationConfig(
            duration=time,
            simulation_interface=LoopbackInterface(
                [("con1", 1, "con1", 1), ("con1", 2, "con1", 1)],
                latency=self.time_of_flight,
                noisePower=0.2 ** 2,
            ),
        )
        return simulation_config

    def _qua_program(self, simulate: bool = False, use_opt_weights: bool = False):
        """Return the qm program that prepare the ground state and the excited state in one loop respectively.

        Args:
        simulate [bool]: if the simulate is True, the program will use pre-defined ``readout_pulse_g`` waveform to simulate the returning waveform that correspondings to a measurement on the ground state of the qubit.
        Conversely, the program will use pre-defined  ``readout_pulse_e`` waveform to itimiate a measurement on the excited stte of the qubit.
        use_op_weights [bool]: if False, we use the readout pulse given by ``self.readout pulse`` attribute (rectangular pulse
                               by default), if True, optimal integration weights are used.
        """
        if use_opt_weights:
            weight_cos = self.opt_iw_cos
            weight_sin = self.opt_iw_sin
        else:
            weight_cos = self.iw_cos
            weight_sin = self.iw_sin

        if simulate:
            readout_pulse_g = "readout_pulse_g"
            readout_pulse_e = "readout_pulse_e"
        else:
            readout_pulse_g = self.readout_pulse
            readout_pulse_e = self.readout_pulse

        thres = self.get_threshold()

        with program() as test_program:
            n = declare(int)
            Ig = declare(fixed)
            Qg = declare(fixed)
            Ie = declare(fixed)
            Qe = declare(fixed)
            resg = declare(bool)
            rese = declare(bool)
            is_simulated = declare(bool, value=simulate)
            threshold = declare(fixed, value=thres)

            adcg = declare_stream(adc_trace=True)
            adce = declare_stream(adc_trace=True)

            with for_(n, 0, n < self.N + 1 / 2, n + 1):

                align(self.qubit, self.resonator)
                measure(
                    readout_pulse_g,
                    self.resonator,
                    adcg,
                    demod.full(weight_cos, Ig, self.analog_input),
                    demod.full(weight_sin, Qg, self.analog_input),
                )
                assign(resg, Ig > threshold)

                save(resg, "resg")
                save(Ig, "Ig")
                save(Qg, "Qg")
                wait(self.wait_time, self.resonator)

                # if not be simualted
                with if_(~is_simulated):
                    play(self.qubit_pulse, self.qubit)
                align(self.qubit, self.resonator)
                measure(
                    readout_pulse_e,
                    self.resonator,
                    adce,
                    demod.full(weight_cos, Ie, self.analog_input),
                    demod.full(weight_sin, Qe, self.analog_input),
                )
                assign(rese, Ie > threshold)

                save(rese, "rese")
                save(Ie, "Ie")
                save(Qe, "Qe")
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

    def _execute_and_fetch(self, program, simulation_config=None, **execute_args):
        """Execute an fetch the data from the OPX."""
        qm = self.qmm.open_qm(self.config)

        # use simualtor
        if simulation_config is not None:
            job = qm.simulate(program, simulate=simulation_config)
        else:
            job = qm.execute(program, **execute_args)

        res = job.result_handles
        res.wait_for_all_values()

        Ig_res = res.get("Ig").fetch_all()["value"]
        Ie_res = res.get("Ie").fetch_all()["value"]
        # sine we measure the ground state once and the excited state once in one loop
        # we discriminate these results alternatively to match the states represented by seq0
        I_res = np.concatenate((Ig_res, Ie_res), axis=0)

        Qg_res = res.get("Qg").fetch_all()["value"]
        Qe_res = res.get("Qe").fetch_all()["value"]
        # sine we measure the ground state once and the excited state once in one loop
        # we discriminate these results alternatively to match the states represented by seq0
        Q_res = np.concatenate((Qg_res, Qe_res), axis=0)

        if I_res.shape != Q_res.shape:
            raise RuntimeError("I and Q shape does mot match")

        timestamps_g = res.get("timestamps_g").fetch_all()["value"]
        timestamps_e = res.get("timestamps_e").fetch_all()["value"]
        timestamps = np.concatenate((timestamps_g, timestamps_e), axis=0)

        adc_g = res.get("adc_g").fetch_all()["value"]
        adc_e = res.get("adc_e").fetch_all()["value"]

        adc = np.concatenate((adc_g, adc_e), axis=0)

        rese = res.get("rese").fetch_all()["value"]
        resg = res.get("resg").fetch_all()["value"]
        res = np.concatenate((rese, resg), axis=0)

        measures_per_state = len(I_res) // self.num_of_states
        # seq0 is 1-dimentional array [0,0...,1,1,...,2,2,...]
        # representing the expected state
        seq0 = np.array(
            [[i] * measures_per_state for i in range(self.num_of_states)]
        ).flatten()

        return I_res, Q_res, timestamps, adc, res

    def get_threshold(self):
        """Get the threshold from the stored data. The threshold is defined as the difference of the bias of the traces
        for different qubit states.
        """
        if self.saved_data:
            bias = self.saved_data["bias"]
            return bias[0] - bias[1]
        else:
            return 0

    def test_after_train(
        self,
        program=None,
        simulate=False,
        simulation_config=None,
        plot=True,
        **execute_args,
    ) -> None:
        """Perfrom the test program after discriminating the optimal integration weights."""
        # use optimal weight coefficients
        if program is None:
            program = self._qua_program(simulate=simulate, use_opt_weights=True)

        if simulate and simulation_config is None:
            simulation_config = self._simulation_config()

        results = self._execute_and_fetch(
            program, simulation_config=simulation_config, **execute_args
        )
        I_res, Q_res, res = results[0], results[1], results[4]

        measures_per_state = len(I_res) // self.num_of_states

        # seq0 is 1-dimentional array [0,0...,1,1,...,2,2,...]
        # representing the expected state
        seq0 = np.array(
            [[i] * measures_per_state for i in range(self.num_of_states)]
        ).flatten()

        weights = self.saved_data["weights"]
        bias = self.saved_data["bias"]
        thres = bias[0] - bias[1]
        b_vec = weights[0, :] - weights[1, :]

        if plot:

            plt.figure()
            plt.title("The discrimination of the states by I Q")
            plt.hist(I_res[np.array(seq0) == 0], 50)
            plt.hist(I_res[np.array(seq0) == 1], 50)
            plt.plot([self.get_threshold()] * 2, [0, 60], "g")
            plt.show()

            plt.figure()
            plt.title("The IQ with optimal weights")
            for i in range(self.num_of_states):
                I_ = I_res[seq0 == i]
                Q_ = Q_res[seq0 == i]
                plt.plot(I_, Q_, ".", label=f"state {i}")
                plt.axis("equal")
            plt.xlabel("I")
            plt.ylabel("Q")
            plt.legend()

            p_s = np.zeros(shape=(2, 2))
            for i in range(2):
                res_i = res[np.array(seq0) == i]
                p_s[i, :] = np.array([np.mean(res_i == 0), np.mean(res_i == 1)])
            labels = ["g", "e"]

            plt.figure()
            ax = plt.subplot()
            sns.heatmap(p_s, annot=True, ax=ax, fmt="g", cmap="Blues")

            ax.set_xlabel("Predicted labels")
            ax.set_ylabel("Prepared labels")
            ax.set_title("Confusion Matrix")
            ax.xaxis.set_ticklabels(labels)
            ax.yaxis.set_ticklabels(labels)
            plt.show()
