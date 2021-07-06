""" Test server that serves qcrew's instruments for remote calls """

from pathlib import Path
from typing import Any

import Pyro5.api as pyro
import qcrew.helpers.yamlizer as yml
from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger

from tests.test_labbrick import TestLabBrick


@pyro.expose
class TestServer:
    """ """

    configpath: Path = Path("C:/Users/athar/qcrew/tests/test_config.yml")
    port_num: int = 9090
    servername: str = "testserver"

    def __init__(self, daemon: pyro.Daemon) -> None:
        """ """
        self._daemon = daemon
        self._config: dict[str, Any] = None  # updated by _load()
        self._load()
        self._expose()
        self.uri: pyro.URI = None  # updated by _serve()
        self._services: dict[Any, str] = dict()  # updated by _serve()
        self._serve()

    def _load(self) -> list[Instrument]:
        """Load instruments from configpath"""
        logger.info("Loading config...")
        self._config = yml.load(self.configpath)
        instruments, modespec = self._config["instruments"], self._config["modes"]
        logger.success(f"Found {len(instruments)} instruments, {len(modespec)} modes")

    def _expose(self) -> None:
        """Expose unique instrument classes found in config"""
        classes = {instrument.__class__ for instrument in self._config["instruments"]}
        for class_ in classes:
            pyro.expose(class_)
        logger.success(f"Exposed {len(classes)} instrument class(es): {classes}")

    def _serve(self) -> None:
        """Register instrument instances and self with daemon and storing uris"""
        for instrument in self._config["instruments"]:
            uri = self._daemon.register(instrument, objectId=str(instrument))
            self._services[instrument.id] = str(uri)
            logger.success(f"Registered {instrument} at {uri}")
        self.uri = self._daemon.register(self, objectId=self.servername)
        logger.success(f"Registered self at {self.uri}")

    @property  # modespec getter
    def modespec(self) -> dict[str, Any]:
        """ """
        return self._config["modes"].copy()

    @modespec.setter
    def modespec(self, new_modespec: dict[str, Any]) -> None:
        """ """
        mode_config = self._config["modes"]
        for mode_name in mode_config:
            mode_config[mode_name]["parameters"] = new_modespec[mode_name]

    @property  # services getter
    def services(self) -> dict[Any, str]:
        """ """
        return self._services.copy()

    def save(self) -> None:
        """Save instruments and modes to configpath"""
        logger.info("Saving to config...")
        yml.save(self._config, self.configpath)

    def shutdown(self) -> None:
        """Disconnect instruments and shutdown daemon"""
        logger.info("Disconnecting instruments...")
        for instrument in self._config["instruments"]:
            instrument.disconnect()
        logger.info(f"Shutting down {self}...")
        self._daemon.shutdown()

    @classmethod
    def get_uri(cls) -> str:
        """ """
        return f"PYRO:{cls.servername}@localhost:{cls.port_num}"

if __name__ == "__main__":
    logger.info("Initializing daemon and server...")
    daemon_ = pyro.Daemon(port=TestServer.port_num)
    server = TestServer(daemon=daemon_)
    with daemon_:
        logger.info("Starting daemon request loop...")
        daemon_.requestLoop()
        logger.info("Exited daemon request loop")
