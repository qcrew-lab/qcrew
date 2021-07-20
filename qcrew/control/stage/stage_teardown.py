""" """

import time

import Pyro5.api as pyro
from qcrew.control.stage.stage import RemoteStage
from qcrew.helpers import logger

if __name__ == "__main__":
    logger.info("Tearing down remote stage, no action needed, just wait ~3s...")
    with pyro.Proxy(RemoteStage.get_uri()) as remote_stage:
        remote_stage.teardown()
    time.sleep(3)
