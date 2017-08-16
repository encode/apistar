import os
import sys

import pytest

from apistar.exceptions import ConfigurationError


def test() -> None:  # pragma: nocover
    """
    Run the test suite.
    """
    file_or_dir = []
    if os.path.exists('tests'):
        file_or_dir.append('tests')
    if os.path.exists('tests.py'):
        file_or_dir.append('tests.py')
    if not file_or_dir:
        raise ConfigurationError("No 'tests/' directory or 'tests.py' module.")

    exitcode = pytest.main(list(file_or_dir))
    if exitcode:
        sys.exit(exitcode)
