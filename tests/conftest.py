from typing import Callable

from pathlib import Path

import pytest

from ftp_loader.utils.resource import filename_resolver


@pytest.fixture(scope="session")
def data() -> Callable[[str], str]:
    return filename_resolver("tests")
