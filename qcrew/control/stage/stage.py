""" """

from pathlib import Path
from qcrew.control.modes.mode import Mode
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder

import Pyro5.api as pyro
import qcrew.helpers.yamlizer as yml
from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger
from qm.QuantumMachine import QuantumMachine
from qm.QuantumMachinesManager import QuantumMachinesManager


class Stage:
    """ """

    def __init__(self, configpath: Path, has_qm: bool = False) -> None:
        """ """
        self._configpath = configpath
        self._config = dict()  # updated by _load()
        self._load()

        self._has_qm = has_qm
        if self._has_qm:  # the stage has a QuantumMachine
            self._qmm = QuantumMachinesManager()
            config_objects = self._config.values()
            self.modes = (v for v in config_objects if isinstance(v, Mode))
            logger.success(f"Found {len(self.modes)} modes")
            self._qcb = QMConfigBuilder(*self.modes)

    def _load(self) -> None:
        """ """
        filename = self._configpath.name
        logger.info(f"Loading objects from {filename}...")
        raw_config = yml.load(self._configpath)

        try:
            for object_ in raw_config:
                name = object_.name
                self._config[name] = object_
                logger.success(f"Staged object of {type(object_)} with {name = }")
        except (TypeError, AttributeError):
            logger.error(f"{filename} must have a sequence of objects with a `.name`")
            raise
        else:
            if len(raw_config) != len(self._config):
                logger.error(f"Two objects in {filename} must not have identical names")
                raise ValueError(f"Duplicate name found in {filename}")

    def save(self) -> None:
        """ """
        logger.info(f"Saving staged objects to {self._configpath.name}...")
        raw_config = list(self._config.values())
        yml.save(raw_config, self._configpath)

    @property  # stage config getter
    def config(self) -> dict:
        """ """
        return self._config.copy()

    @property  # qm getter
    def qm(self) -> QuantumMachine:
        """ """
        if not self._has_qm:
            logger.error("Re-initialize stage with `has_qm = True` to get a QM")
            raise AttributeError("Stage not initialized with QM")
        qm = self._qmm.open_qm(self._qcb.config)
        return qm

@pyro.expose
class RemoteStage(Stage):
    """ """

    port_num: int = 9090
    servername: str = "remote_stage"

    def __init__(self, daemon: pyro.Daemon, configpath: Path) -> None:
        """ """
        super().__init__(configpath=configpath)

        remote_objects = self._config.values()
        self._instruments = (v for v in remote_objects if isinstance(v, Instrument))

        self._daemon = daemon
        # self._services: dict[str, str] = dict()  # updated by _serve()
        self._serve()

    def _serve(self) -> None:
        """ """
        for name, object_ in self._config.items():
            uri = self._daemon.register(object_, objectId=name)
            # self._services[name] = str(uri)
            logger.success(f"Registered {object_} at {uri}")

    @classmethod
    def get_uri(cls) -> str:
        """ """
        return f"PYRO:{cls.servername}@localhost:{cls.port_num}"

    # @property  # services getter
    # def services(self) -> dict[str, str]:
    # """ """
    # return self._services.copy()

    @property  # instruments getter
    def instruments(self) -> set[Instrument]:
        """ """
        return tuple(self._instruments)

    def teardown(self) -> None:
        """ """
        self.save()

        logger.info("Disconnecting instruments...")
        for instrument in self._instruments:
            instrument.disconnect()

        logger.info("Shutting down daemon...")
        self._daemon.shutdown()
