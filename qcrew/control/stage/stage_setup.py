""" """

from pathlib import Path

import Pyro5.api as pyro
import qcrew.control.instruments as qci
from qcrew.control.stage.stage import RemoteStage
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
import qcrew.helpers.yamlizer as yml

_CONFIGPATH = Path("C:/Users/qcrew/qcrew/qcrew/config/stage.yml")
_REMOTE_CONFIGPATH = Path(yml.load(_CONFIGPATH)["remote"])

if __name__ == "__main__":
    remote_classes = {Parametrized, qci.Instrument, qci.LabBrick, qci.Sa124}
    for remote_class in remote_classes:
        pyro.expose(remote_class)
    logger.debug(f"Exposed qcrew classes: {[cls_.__name__ for cls_ in remote_classes]}")

    daemon_ = pyro.Daemon(port=RemoteStage.port_num)
    stage = RemoteStage(daemon=daemon_, configpath=_REMOTE_CONFIGPATH)
    self_uri = daemon_.register(stage, objectId=stage.servername)
    logger.success(f"Served remote stage at {self_uri}")

    with daemon_:
        logger.info("Remote stage setup complete! Now listening for requests...")
        daemon_.requestLoop()
        logger.debug("Exited daemon request loop")
