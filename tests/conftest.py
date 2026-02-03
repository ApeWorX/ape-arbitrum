import ape
import pytest


@pytest.fixture(autouse=True)
def eth_tester_provider():
    if not ape.networks.active_provider or ape.networks.provider.name != "test":
        with ape.networks.arbitrum.local.use_provider("test") as provider:
            yield provider
    else:
        yield ape.networks.provider


@pytest.fixture
def networks():
    return ape.networks


@pytest.fixture
def accounts():
    return ape.accounts


@pytest.fixture
def Contract():
    return ape.Contract


@pytest.fixture
def arbitrum(networks):
    return networks.arbitrum


@pytest.fixture
def account(accounts):
    return accounts.test_accounts[0]


@pytest.fixture
def second_account(accounts):
    return accounts.test_accounts[1]
