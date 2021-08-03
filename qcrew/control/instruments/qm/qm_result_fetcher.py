""" """

from typing import Callable

from qm._results import MultipleNamedJobResult, SingleNamedJobResult
from qm.QmJob import JobResults


class QMResultFetcher:
    """ """

    def __init__(self, handle: JobResults) -> None:
        """ """
        self._handle: JobResults = handle
        self._result_spec: dict[str, Callable] = {"single": dict(), "multiple": dict()}

        if self._handle.is_processing():  # determine fetch mode - live or not live
            self._is_live: bool = True
            self.is_fetching: bool = True  # to indicate live fetching status
            self.count: int = 0  # current number of results fetched
            self._last_count: int = None  # only used in live fetch mode
            self._set_result_spec()
        else:
            self._is_live = False
            self.is_fetching, self.count, self._last_count = None, None, None

    def _set_result_spec(self):
        """ """
        for tag, result in self._handle:
            if isinstance(result, SingleNamedJobResult):
                self._result_spec["single"][tag] = self._fetch_single
            elif isinstance(result, MultipleNamedJobResult):
                if self._is_live:
                    self._result_spec["multiple"][tag] = self._fetch_batch
                else:
                    self._result_spec["multiple"][tag] = self._fetch_multiple
                result.wait_for_values(2)  # so that std err can be calculated

    def fetch(self) -> dict[str, list]:
        """ """
        if self._is_live:  # track live fetch mode attributes
            self._last_count = self.count  # update counts
            self.count = self._count_results()
            if self.count == self._last_count:  # no new results to fetch
                if not self._handle.is_processing():
                    self.is_fetching, self._is_live = False, False  # live fetch is done
                return dict()  # return empty dict because no new results to fetch
        else:
            self._set_result_spec()  # set result spec for non-live fetch mode

        results = dict()  # populate and return results dictionary
        for result_spec in self._result_spec.values():
            for tag, method in result_spec.items():
                results[tag] = method(tag)
        return results

    def _count_results(self):
        """ """
        return min(len(self._handle.get(tag)) for tag in self._result_spec["multiple"])

    def _fetch_single(self, tag):
        """ """
        return self._handle.get(tag).fetch_all(flat_struct=True)

    def _fetch_batch(self, tag):
        """ """
        slc = slice(self._last_count, self.count)
        return self._handle.get(tag).fetch(slc, flat_struct=True)

    def _fetch_multiple(self, tag):
        """ """
        return self._handle.get(tag).fetch_all(flat_struct=True)
