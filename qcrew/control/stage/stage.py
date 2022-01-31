""" """

from pathlib import Path

import Pyro5.api as pyro

import qcrew.control.instruments as qci
import qcrew.control.instruments.qm as qciqm
import qcrew.control.modes as qcm
import qcrew.helpers.yamlizer as yml
from qcrew.helpers import logger

from qm.QuantumMachine import QuantumMachine
from qm.QuantumMachinesManager import QuantumMachinesManager


class Stage:
    """ """

    def __init__(self, configpath: Path) -> None:
        """ """
        self._configpath = configpath
        self._config = None  # updated by _setup()

    def _setup(self) -> None:
        """ """
        filename = self._configpath.name
        logger.debug(f"Loading objects from {filename}...")
        self._config = yml.load(self._configpath)

        try:
            object_names = {object_.name for object_ in self._config}
        except (TypeError, AttributeError):
            logger.error(f"{filename} must have a sequence of objects with a `.name`")
            raise
        else:
            if len(object_names) != len(self._config):
                logger.error(f"Two objects in {filename} must not have identical names")
                raise ValueError(f"Duplicate name found in {filename}")

    def teardown(self) -> None:
        """ """
        yml.save(self._config, self._configpath)


class LocalStage(Stage):
    """ """

    def __init__(
        self,
        configpath: Path,
        datapath: Path,
        sample_name: str,
        project_name: str,
        connect_qm: bool,
    ) -> None:
        """ """
        super().__init__(configpath=configpath)
        self.datapath = datapath
        self.sample_name = sample_name
        self.project_name = project_name
        self.modes = None  # updated by _setup()
        self.connect_qm = connect_qm
        self._setup()

    def _setup(self) -> None:
        """ """
        super()._setup()

        if self.connect_qm:
            # NOTE for now, only support staging modes locally
            self.modes = [v for v in self._config if isinstance(v, qcm.Mode)]
            logger.debug(f"Found {len(self.modes)} modes")

            self._qmm = QuantumMachinesManager()
            self._qcb = qciqm.QMConfigBuilder(*self.modes)

    @property  # qm getter
    def QM(self) -> QuantumMachine:
        """ """
        if not self.connect_qm:
            raise RuntimeError(
                "Please set 'qm' to True in stage.yml to connect to QM and re-run 'setup_stage'"
            )
        qm = self._qmm.open_qm(self._qcb.config)
        return qm


@pyro.expose
class RemoteStage(Stage):
    """ """

    port_num: int = 9090
    servername: str = "REMOTE_STAGE"

    def __init__(self, daemon: pyro.Daemon, configpath: Path) -> None:
        """ """
        super().__init__(configpath=configpath)
        self.instruments = None  # updated by _setup()
        self._daemon = daemon
        self._services: dict[str, str] = dict()  # updated by _serve_instruments()
        self._setup()

    def _setup(self) -> None:
        """ """
        super()._setup()

        # NOTE for now, only support serving instruments remotely
        self.instruments = [v for v in self._config if isinstance(v, qci.Instrument)]
        logger.debug(f"Found {len(self.instruments)} instruments")
        self._serve_instruments()

    def _serve_instruments(self) -> None:
        """ """
        for instrument in self.instruments:
            uri = self._daemon.register(instrument, objectId=instrument.name)
            self._services[instrument.name] = str(uri)
            logger.success(f"Served {instrument} at {uri}")

    @classmethod
    def get_uri(cls) -> str:
        """ """
        return f"PYRO:{cls.servername}@localhost:{cls.port_num}"

    @property  # services getter
    def services(self) -> dict[str, str]:
        """ """
        return self._services.copy()

    def teardown(self) -> None:
        """ """
        super().teardown()

        logger.debug("Disconnecting instruments...")
        for instrument in self.instruments:
            instrument.disconnect()

        logger.debug("Shutting down daemon...")
        self._daemon.shutdown()
