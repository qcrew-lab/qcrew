""" """

from pathlib import Path

import Pyro5.api as pyro
from qcrew.control.stage.stage import LocalStage, RemoteStage
from qcrew.control.stage.stage_setup import LOCAL_CONFIGPATH
from qcrew.helpers import logger

# pylint: disable=unused-import, these classes need to be imported for yamlizing to work

from qcrew.control.modes.qubit import Qubit
from qcrew.control.modes.readout import Readout

# pylint: enable=unused-import


class Stagehand:
    """ """

    def __init__(self, configpath: Path = LOCAL_CONFIGPATH) -> None:
        """ """
        self._configpath = configpath
        self.stage: LocalStage = LocalStage(configpath=self._configpath)
        self.proxies = dict()  # update by _stage_remote_objects()

    def __enter__(self) -> LocalStage:
        """ """
        self._stage_local_objects()
        self._stage_remote_objects()
        return self.stage

    def _stage_local_objects(self) -> None:
        """ """
        for mode in self.stage.modes:
            setattr(self.stage, mode.name, mode)
            logger.success(f"Set stage attribute '{mode.name}'")

    def _stage_remote_objects(self) -> None:
        """ """
        with pyro.Proxy(RemoteStage.get_uri()) as remote_stage:

            for name, uri in remote_stage.services.items():
                instrument_proxy = pyro.Proxy(uri)
                logger.success(f"Connected to remote instrument with {name = }")
                self.proxies[name] = instrument_proxy
                setattr(self.stage, name, instrument_proxy)
                logger.success(f"Set stage attribute '{name}'")

            for mode in self.stage.modes:
                lo_name = mode.lo
                if lo_name in self.proxies:
                    mode.lo = self.proxies[lo_name]
                    logger.success(f"Connected {lo_name} as {mode.name} lo")

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """ """
        for mode in self.stage.modes:
            mode.lo = mode.lo.name
        self.stage.teardown()
