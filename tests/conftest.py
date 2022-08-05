import pytest


@pytest.fixture
def networks():
    from ape import networks

    return networks


@pytest.fixture
def accounts():
    from ape import accounts

    return accounts


@pytest.fixture
def Contract():
    from ape import Contract

    return Contract
