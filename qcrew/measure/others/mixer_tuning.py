""" mixer tuning v5 """

from qcrew.control.instruments.meta.mixer_tuner import MixerTuner
from qcrew.control.instruments.meta.yale_mixer_tuner import YaleMixerTuner
from qcrew.control import Stagehand

if __name__ == "__main__":
    with Stagehand() as stage:
        sa, qubit = stage.SA, stage.QUBIT
        # get an already configured qm after making changes to modes
        qm = stage.QM

        # set this to True to run the brute-force minimizer
        # set to False to run the Nelder-Mead minimizer
        run_yale_algo = False

        if run_yale_algo:
            # select which mode object you want to tune
            mode = qubit

            ymxrtnr = YaleMixerTuner(mode, sa=sa, qm=qm)

            # these are run parameters for tuning LO leakage

            # range of DC offsets you want to sweep to tune LO
            dc_offsets_range = (-0.05, 0.05)  # (min = -0.5, max = 0.5)
            # number of DC offset sweep points in the given range i.e. decide step size
            num_dc_offsets = 7
            # number of iterations of the minimization you want to run
            lo_iterations = 5
            # after each iteration, the sweep range will be reduced by this factor
            lo_range_div = 2

            ymxrtnr.minimize_lo_leakage(
                *dc_offsets_range,
                n_it=lo_iterations,
                n_eval=num_dc_offsets,
                range_div=lo_range_div,
                verbose=True,
                plot=True,
            )

            # these are run parameters for tuning SB leakage
            # range of SB tuning offsets you want to sweep to tune SB
            sb_offsets_range = (-0.5, 0.5)  # (min =, max =)
            # number of offset sweep points in the given range i.e. decide step size
            num_sb_offsets = 11
            # number of iterations of the minimization you want to run
            sb_iterations = 5
            # after each iteration, the sweep range will be reduced by this factor
            sb_range_div = 2

            ymxrtnr.minimize_sb_leakage(
                *sb_offsets_range,
                n_it=sb_iterations,
                n_eval=num_sb_offsets,
                range_div=sb_range_div,
                verbose=True,
                plot=True,
            )
        else:
            mxrtnr = MixerTuner(qubit, sa=sa, qm=qm)
            mxrtnr.tune()

            # run this to find the minimization landscape
            #mxrtnr.landscape(
            #    mode=qubit, key="LO", xlim=(-0.4, 0.4), ylim=(-0.4, 0.4), points=51
            #)
