import pytest
from ape_ethereum.transactions import TransactionType


def test_gas_limit(arbitrum):
    assert arbitrum.config.local.gas_limit == "max"


@pytest.mark.parametrize("type", (0, "0x0"))
def test_create_transaction(arbitrum, type):
    txn = arbitrum.create_transaction(type=type)
    assert txn.type == TransactionType.STATIC.value
