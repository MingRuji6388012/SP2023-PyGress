# -*- coding: utf-8 -*-

"""Processor for remote INDRA JSON files."""

from collections import Counter

import requests
from typing import List

from ..statements import Statement, stmts_from_json

__all__ = [
    'RemoteProcessor',
]


class RemoteProcessor:
    """A processor for INDRA JSON file to be retrieved by URL.

    Parameters
    ----------
    url :
        The URL of the INDRA JSON file to load
    """

    #: The URL of the data
    url: str

    def __init__(self, url: str):
        self.url = url
        self._statements = None

    @property
    def statements(self) -> List[Statement]:
        """The extracted statements."""
        if self._statements is None:
            self.extract_statements()
        return self._statements

    def extract_statements(self) -> List[Statement]:
        """Extract statements from the remote JSON file."""
        res = requests.get(self.url)
        res.raise_for_status()
        self._statements = stmts_from_json(res.json())
        return self._statements

    def print_summary(self) -> None:
        """print a summary of the statements."""
        from tabulate import tabulate
        print(tabulate(
            Counter(
                statement.__class__.__name__
                for statement in self.statements
            ).most_common(),
            headers=["Statement Type", "Count"],
        ))