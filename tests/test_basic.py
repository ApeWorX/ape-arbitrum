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


def test_basic(accounts, networks):

    with networks.arbitrum.local.use_provider("test"):
        a = accounts.test_accounts[0]
        a.transfer(a, 100)
