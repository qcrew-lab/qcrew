""" """

from pathlib import Path
from typing import Any

import Pyro5.api as pyro
import qcrew.helpers.yamlizer as yml
from qcrew.control.instruments.instrument import Instrument
from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.instruments.vaunix.labbrick import LabBrick
import qcrew.control.instruments.quantum_machines.qm_config_builder as qcb
from qcrew.control.modes.mode import Mode, ReadoutMode
from qcrew.control.modes.qubit import Qubit
from qcrew.control.modes.readout_resonator import ReadoutResonator
from qcrew.control.pulses.pulses import ConstantPulse, GaussianPulse, Pulse
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qm.QuantumMachine import QuantumMachine
from qm.QuantumMachinesManager import QuantumMachinesManager

# TODO make configpath absolute
CONFIGPATH = Path("C:/Users/qcrew/qcrew-dev/tests/test_stage.yml")


@pyro.expose
class Stage:
    """ """

    port_num: int = 9090
    servername: str = "stage"

    def __init__(self, daemon: pyro.Daemon, configpath: Path) -> None:
        """ """
        self._daemon = daemon
        self._configpath = configpath
        self._config: dict[str, Any] = dict()  # updated by _load()
        self._modes: list(Mode) = []  # updated by _load()
        self._load()

        self._config_builder = None
        if self._modes:
            self._config_builder = qcb.QMConfigBuilder(*self._modes)

        self.uri: pyro.URI = None  # updated by _serve()
        self._services: dict[str, str] = dict()  # updated by _serve()
        self._serve()

    def _load(self) -> None:
        """ """
        logger.info(f"Loading remote objects from {self._configpath.name}...")
        raw_config = yml.load(self._configpath)  # TODO error handling
        try:
            for remote_object in raw_config:
                name = remote_object.name
                self._config[name] = remote_object
                if isinstance(remote_object, Mode):
                    self._modes.append(remote_object)
                logger.success(f"Found object of {type(remote_object)} with {name = }")
        except TypeError:
            logger.exception("Expect config data to be an iterable of remote objects")
            raise
        except AttributeError:
            logger.exception("All remote objects must have a `.name` attribute")
            raise
        else:
            logger.success(f"Found {len(self._modes)} modes: {self._modes}")

    def _serve(self) -> None:
        """ """
        for name, object_ in self._config.items():
            uri = self._daemon.register(object_, objectId=name)
            self._services[name] = str(uri)
            logger.success(f"Registered {object_} at {uri}")
        self.uri = self._daemon.register(self, objectId=self.servername)
        logger.success(f"Registered stage at {self.uri}")

    @classmethod
    def get_uri(cls) -> str:
        """ """
        return f"PYRO:{cls.servername}@localhost:{cls.port_num}"

    @property  # services getter
    def services(self) -> dict[str, str]:
        """ """
        return self._services.copy()

    @property  # qm config getter
    def qm_config(self) -> qcb.QMConfig:
        """ """
        if self._config_builder is not None:
            return self._config_builder.config
        else:
            logger.warning("Cannot build QM config if no modes exist on stage!")

    def teardown(self) -> None:
        """ """
        self._save()

        logger.info("Disconnecting instruments...")
        for object_ in self._config.items():  # TODO remove isinstance checks
            if isinstance(object_, Instrument):
                object_.disconnect()
            elif isinstance(object_, Mode):
                object_.lo.disconnect()

        logger.info("Shutting down daemon and stage...")
        self._daemon.shutdown()

    def _save(self) -> None:
        """ """
        logger.info("Saving remote objects to config...")
        raw_config = list(self._config.values())
        yml.save(raw_config, self._configpath)


class Stagehand:
    """ """

    def __init__(self) -> None:
        """ """
        self.stage = pyro.Proxy(Stage.get_uri())
        logger.success("Established link to stage")
        self._objspec = self.stage.services
        logger.success(f"Located remote objects: {set(self._objspec)}")

    def link(self, *names: str) -> dict[str, pyro.Proxy]:
        """ """
        stg = dict()
        for name in names:
            if name == "QM":
                stg[name] = self._link_qm()
            elif name in self._objspec:
                uri = self._objspec[name]
                stg[name] = pyro.Proxy(uri)
            else:
                logger.warning(f"Remote object with {name = } does not exist")
        return stg

    def _link_qm(self) -> QuantumMachine:
        """ """
        qmm = QuantumMachinesManager()
        logger.info("Configuring QM...")
        qm_config = self.stage.qm_config
        return qmm.open_qm(qm_config)


if __name__ == "__main__":
    remote_classes = {  # to be exposed for remote calls
        Parametrized,
        LabBrick,
        Sa124,
        Mode,
        ReadoutMode,
        Qubit,
        ReadoutResonator,
        Pulse,
        ConstantPulse,
        GaussianPulse,
    }
    for remote_class in remote_classes:
        pyro.expose(remote_class)
    logger.info(f"Exposed qcrew classes: {[cls_.__name__ for cls_ in remote_classes]}")

    logger.info("Initializing daemon and stage...")
    daemon_ = pyro.Daemon(port=Stage.port_num)
    stage = Stage(daemon=daemon_, configpath=CONFIGPATH)

    with daemon_:
        logger.info("Starting daemon request loop...")
        daemon_.requestLoop()
        logger.info("Exited daemon request loop")
