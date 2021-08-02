""" Qcrew QM result fetcher v1.0 """
from typing import Callable
import numpy as np
from qm.QmJob import JobResults
from qm._results import SingleNamedJobResult, MultipleNamedJobResult


class Fetcher:

    def __init__(self, handle: JobResults, num_results: int) -> None:
        """Initialize a Fetcher instance.

        Args:
            handle (JobResults): QM job result handle
            num_results (int): total number of results expected to be fetched
        """
        self.total_count: int = num_results  # tota number of results to fetch
        self.count: int = 0  # current number of results fetched
        self.last_count: int = None  # last known result count

        self.handle: JobResults = handle
        self._spec: dict[str, Callable] = {"single": dict(), "multiple": dict()}
        self._pre_process_results()

        self.is_fetching: bool = True  # to indicate fetching has started

    def _pre_process_results(self):
        """Categorize the result handles based on their type, so that the appropriate QM API fetch method is called in self.fetch(). Additionally, wait for at least two values to be processed for all MultipleNamedJobResults, so that self.count and self.last_count become meaningful.
        """
        for tag, result in self.handle:
            if isinstance(result, SingleNamedJobResult):
                self._spec["single"][tag] = self._fetch_single
            elif isinstance(result, MultipleNamedJobResult):
                self._spec["multiple"][tag] = self._fetch_multiple
                result.wait_for_values(2)

    def fetch(self) -> tuple:
        """To be called during a live measurement post-processing loop. Fetches the latest available results for all tags in result handle.

        Returns:
            dict[str, np.ndarray]: key -> result handle tag, value -> (1) for MultipleNamedJobResult, value is the numpy array returned by calling handle.get(tag).fetch_all(flat_struct = True). (2) For SingleNamedJobResult, value is the numpy array returned by calling handle.get(tag).fetch_all(flat_struct = True).
        """
        self.last_count = self.count  # get and update counts
        self.count = min(len(self.handle.get(tag)) for tag in self._spec["multiple"])

        if self.count == self.last_count:  # no new results to fetch
            if not self.handle.is_processing() and self.count >= self.total_count:
                self.is_fetching = False  # fetching is complete
                if self.count > self.total_count:
                    print(f"WARNING: EXTRA RESULTS ({self.count}, {self.total_count})")
            return (self.count, dict())  # return empty dict because no new results to fetch

        partial_results = dict()  # populate and return partial results dictionary
        for result_type in self._spec:
            for tag in self._spec[result_type]:
                partial_results[tag] = self._spec[result_type][tag](tag)
        return (self.count, partial_results)

    def _fetch_single(self, tag):
        """ Internal method for dealing with SingleNamedJobResult """
        return self.handle.get(tag).fetch_all(flat_struct=True)

    def _fetch_multiple(self, tag):
        """ Internal method for dealing with MultipleNamedJobResult """
        slc = slice(self.last_count, self.count)
        return self.handle.get(tag).fetch(slc, flat_struct=True)



