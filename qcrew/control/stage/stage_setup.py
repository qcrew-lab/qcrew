""" """

from pathlib import Path

import Pyro5.api as pyro
from qcrew.control.instruments.instrument import Instrument
from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.instruments.vaunix.labbrick import LabBrick
from qcrew.control.stage.stage import RemoteStage
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized


LOCAL_CONFIGPATH = Path("C:/Users/qcrew/qcrew-dev/configs/modes.yml")
""" Path to the yml config containing modes to be instantiated locally """

REMOTE_CONFIGPATH = Path("C:/Users/qcrew/qcrew-dev/configs/instruments.yml")
""" Path to the yml config containing instruments to be served remotely """

if __name__ == "__main__":

    remote_classes = {Parametrized, Instrument, LabBrick, Sa124}
    for remote_class in remote_classes:
        pyro.expose(remote_class)
    logger.info(f"Exposed qcrew classes: {[cls_.__name__ for cls_ in remote_classes]}")

    logger.info("Initializing daemon...")
    daemon_ = pyro.Daemon(port=RemoteStage.port_num)
    stage = RemoteStage(daemon=daemon_, configpath=REMOTE_CONFIGPATH)
    self_uri = daemon_.register(stage, objectId=stage.servername)
    logger.success(f"Registered remote stage at {self_uri}")

    with daemon_:
        logger.info("Starting daemon request loop...")
        daemon_.requestLoop()
        logger.info("Exited daemon request loop")
