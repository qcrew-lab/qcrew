""" """

from pathlib import Path

import Pyro5.api as pyro
from qcrew.control.stage.stage import RemoteStage, Stage
from qcrew.control.stage.stage_setup import LOCAL_CONFIGPATH
from qcrew.helpers import logger


class Stagehand:
    """ """

    def __init__(self, configpath: Path = LOCAL_CONFIGPATH) -> None:
        """ """
        self._configpath = configpath
        self.stage: Stage = Stage(configpath=self._configpath, has_qm=True)

    def __enter__(self) -> Stage:
        """ """
        self._stage_local_objects()
        self._stage.remote_objects()
        return self.stage

    def _stage_local_objects(self) -> None:
        """ """
        local_config = self.stage.config
        for local_object_name, local_object in local_config.items():
            setattr(self.stage, local_object_name, local_object)
            logger.success(f"Set stage attribute '{local_object_name}'")

    def _stage_remote_objects(self) -> None:
        """ """
        with pyro.Proxy(RemoteStage.get_uri()) as remote_stage:
            instruments = remote_stage.instruments
            logger.success(f"Located {len(instruments)} remote instruments")
            instrument_ids = tuple(instrument.id for instrument in instruments)

            for mode in self.stage.modes:
                id_ = mode.lo
                if id_ in instrument_ids:
                    proxy = instruments[instrument_ids.index(id_)]
                    mode.lo = proxy
                    logger.success(f"Linked {mode.name} & {proxy.name} with id = {id_}")

            for name, proxy in remote_stage.config.items():
                setattr(self.stage, name, proxy)
                logger.success(f"Set stage attribute '{name}'")

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """ """
        self.stage.save()
        logger.info("Releasing proxies...")
        with pyro.Proxy(RemoteStage.get_uri()) as remote_stage:
            for proxy in remote_stage.config.values():
                proxy._pyroRelease()
