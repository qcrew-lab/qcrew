""" """

from pathlib import Path

import Pyro5.api as pyro

from qcrew.control.stage.stage import LocalStage, RemoteStage
from qcrew.helpers import logger
import qcrew.helpers.yamlizer as yml

# pylint: disable=unused-import, these imports are needed for yamlizing to work

import qcrew.control.modes

# pylint: enable=unused-import

_CONFIGPATH = Path("C:/Users/qcrew/qcrew/qcrew/config/stagepaths.yml")
_LOCAL_CONFIGPATH = Path(yml.load(_CONFIGPATH)["local"])

class Stagehand:
    """ """

    def __init__(self, configpath: Path = _LOCAL_CONFIGPATH) -> None:
        """ """
        self._configpath = configpath
        self.stage: LocalStage = LocalStage(configpath=self._configpath)
        self.proxies = dict()  # update by _stage_remote_objects()
        self._stage_local_objects()
        self._stage_remote_objects()

    def __enter__(self) -> LocalStage:
        """ """
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
                logger.debug(f"Connected to remote instrument with {name = }")
                self.proxies[name] = instrument_proxy
                setattr(self.stage, name, instrument_proxy)
                logger.success(f"Set stage attribute '{name}'")

            for mode in self.stage.modes:
                lo_name = mode.lo
                if lo_name in self.proxies:
                    mode.lo = self.proxies[lo_name]
                    logger.debug(f"Connected {lo_name} as {mode.name} lo")

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """ """
        for mode in self.stage.modes:
            mode.lo = mode.lo.name
        self.stage.teardown()
