import pytest
from ethpm_types import HexBytes

from ape_arbitrum.ecosystem import ArbitrumReceipt, ArbitrumTransactionType


def test_gas_limit(arbitrum):
    assert arbitrum.config.local.gas_limit == "max"


@pytest.mark.parametrize("type", (0, "0x0"))
def test_create_transaction(arbitrum, type):
    tx = arbitrum.create_transaction(type=type)
    assert tx.type == ArbitrumTransactionType.STATIC.value


def test_internal_tx(arbitrum):
    tx = arbitrum.create_transaction(type=106)
    assert tx.type == ArbitrumTransactionType.INTERNAL.value


def test_decode_receipt(arbitrum):
    data = {
        "required_confirmations": 0,
        "blockHash": HexBytes("0x01b9030516454bbb3d846bfa31fca8bf5cbdfb735879dcee27fd61f2ae3776b3"),
        "blockNumber": 121166619,
        "hash": HexBytes("0x8b8c74711aa2e117a307f8a96a93350e5ca7e01a7bf39dbb7a824e6a6fc3736f"),
        "chainId": 42161,
        "from": "0x00000000000000000000000000000000000A4B05",
        "gas": 0,
        "gasPrice": 0,
        "input": HexBytes(
            "0x6bf6a42d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011148fc000000000000000000000000000000000000000000000000000000000738db1b0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
        "nonce": 0,
        "r": HexBytes("0x00"),
        "s": HexBytes("0x00"),
        "to": "0x00000000000000000000000000000000000A4B05",
        "transactionIndex": 0,
        "type": 106,
        "v": 0,
        "value": 0,
        "transactionHash": HexBytes(
            "0x8b8c74711aa2e117a307f8a96a93350e5ca7e01a7bf39dbb7a824e6a6fc3736f"
        ),
        "logs": [],
        "contractAddress": None,
        "effectiveGasPrice": 100000000,
        "cumulativeGasUsed": 0,
        "gasUsed": 0,
        "logsBloom": HexBytes(
            "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
        "status": 1,
        "l1BlockNumber": "0x11148fc",
        "gasUsedForL1": "0x0",
    }
    actual = arbitrum.decode_receipt(data)
    assert isinstance(actual, ArbitrumReceipt)
