from typing import Callable

# noinspection PyPackageRequirements
import pytest

from ftp_loader.utils.resource import filename_resolver


@pytest.fixture(scope="session")
def data() -> Callable[[str], str]:
    return filename_resolver("tests")
