""" """

from datetime import datetime
import pathlib

import h5py


class VNADataSaver:
    """ """

    def __init__(
        self,
        datapath: pathlib.Path,
        measurementname: str,
        usersuffix: str,
        datasets,
        datashape,
        datagroup: str = "/",
        datatype: str = "f8",
    ) -> None:
        """ """
        date, time = datetime.now().strftime("%Y%m%d %H%M%S").split()
        filename = f"{time}_{measurementname}_{usersuffix}.hdf5"
        filedir = datapath / date
        filedir.mkdir(parents=True, exist_ok=True)
        filepath = filedir / filename

        self.datafile = h5py.File(str(filepath), "a")
        self.datagroup = datagroup
        self.datatype = datatype
        self.datasets = {}
        for datasetname in datasets:
            name = f"{datagroup}/{datasetname}"
            dataset = self.datafile.create_dataset(
                name=name, shape=datashape, dtype=datatype
            )
            self.datasets[datasetname] = dataset
        self.datafile.flush()

    def __enter__(self):
        """ """
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """ """
        self.datafile.flush()
        self.datafile.close()

    def save_metadata(self, metadatadict) -> None:
        """ """
        for key, value in metadatadict.items():
            try:
                self.datafile.attrs[key] = value
            except TypeError:
                pass
                #print(f"WARNING! Unable to save {key = }, {value = } as metadata")
        self.datafile.flush()

    def save_data(self, data, pos=None) -> None:
        """ """
        for name, datastream in data.items():
            if pos is None:  # create new dataset
                name, dtype = f"{self.datagroup}/{name}", self.datatype
                self.datafile.create_dataset(name=name, data=datastream, dtype=dtype)
            # insert into existing dataset at given pos
            else:
                dataset = self.datasets[name]
                if len(pos) == 1:
                    rep_count = (*pos,)
                    dataset[rep_count] = datastream
                elif len(pos) == 2:
                    rep_count, power_count = pos
                    dataset[rep_count, power_count] = datastream
                else:
                    raise RuntimeError(f"WE DO NOT DO {len(pos)}D SWEEPS HERE...")
        self.datafile.flush()
