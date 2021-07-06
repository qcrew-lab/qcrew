""" """

from pathlib import Path
import Pyro5.api as pyro
import qcrew.helpers.yamlizer as yml
from qcrew.control.instruments.instrument import Instrument


@pyro.expose
class Stage:
    """ """

    configpath: Path = Path.cwd() / "config/config.yml"
    port_num: int = 9090

    def __init__(self, daemon: pyro.Daemon) -> None:
        """ """
        self.name: str = self.__class__.__name__.lower()
        self._daemon = daemon
        self._config = yml.load(self.configpath)
        self.instruments: list[Instrument] = self._config["instruments"]

        classes = {instrument.__class__ for instrument in self.instruments}
        for class_ in classes:
            pyro.expose(class_)


class Stagehand:
    """ """

    pass


if __name__ == "__main__":
    daemon_ = pyro.Daemon(port=Stage.port_num)
    stage = Stage(daemon=daemon_)
    services = {instrument: str(instrument) for instrument in stage.instruments}
    services[stage] = stage.name
    with daemon_:
        pyro.serve(services, daemon=daemon_, use_ns=False)
