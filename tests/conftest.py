import pytest

from fedramp_docs_mcp import loader


@pytest.fixture
def frmr():
    return loader.load_frmr()


@pytest.fixture
def source_version():
    return loader.load_source_version()
