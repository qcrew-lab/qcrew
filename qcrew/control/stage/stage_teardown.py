""" """

import Pyro5.api as pyro
from qcrew.control.stage.stage import RemoteStage

with pyro.Proxy(RemoteStage.get_uri()) as remote_stage:
    remote_stage.teardown()
