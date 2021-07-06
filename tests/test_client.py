""" Test client to mediate interactions between the test server and the experimenter """

import Pyro5.api as pyro
from tests.test_server import TestServer
from tests.test_mode import TestMode, TestReadoutMode
from qcrew.helpers import logger


class TestClient:
    """ """

    mode_map: dict[str, type] = {
        "TestMode": TestMode,
        "TestReadoutMode": TestReadoutMode,
    }

    def __init__(self) -> None:
        """ """
        self.server = pyro.Proxy(TestServer.get_uri())
        logger.success("Located testserver proxy")
        self.modes: list[TestMode] = list()  # updated by _create_modes()
        self._create_modes()

    def _create_modes(self) -> None:
        """ """
        with self.server:
            modespec = self.server.modespec
            services = self.server.services
            logger.info(f"Found {len(modespec)} modes, {len(services)} services")

            for mode_name in modespec:
                mode_dict = modespec[mode_name]
                uri = services[mode_dict["id"]]
                remote = pyro.Proxy(uri)
                mode_cls = self.mode_map[mode_dict["type"]]
                parameters = mode_dict["parameters"]
                mode = mode_cls(name=mode_name, lo=remote, **parameters)
                logger.info(f"Initialized {mode}")
                self.modes.append(mode)

    def sync(self) -> None:
        """ """
        with self.server:
            new_modespec = {mode.name: mode.parameters for mode in self.modes}
            self.server.modespec = new_modespec
            logger.info("Synced all mode parameters with server")
