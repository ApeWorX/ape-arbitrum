import pytest
from ape_ethereum.transactions import TransactionType
from ethpm_types import HexBytes, MethodABI

from ape_arbitrum.ecosystem import INTERNAL_TRANSACTION_TYPE, ArbitrumReceipt


def test_gas_limit(arbitrum):
    assert arbitrum.config.local.gas_limit == "max"


@pytest.mark.parametrize("type", (0, "0x0"))
def test_create_transaction(arbitrum, type, eth_tester_provider):
    tx = arbitrum.create_transaction(type=type)
    assert tx.type == TransactionType.STATIC.value
    assert tx.gas_limit == eth_tester_provider.max_gas


@pytest.mark.parametrize(
    "type_",
    (TransactionType.STATIC.value, TransactionType.DYNAMIC.value, INTERNAL_TRANSACTION_TYPE),
)
def test_encode_transaction(type_, arbitrum, eth_tester_provider):
    abi = MethodABI.parse_obj(
        {
            "type": "function",
            "name": "fooAndBar",
            "stateMutability": "nonpayable",
            "inputs": [],
            "outputs": [],
        }
    )
    address = "0x274b028b03A250cA03644E6c578D81f019eE1323"
    actual = arbitrum.encode_transaction(address, abi, sender=address, type=type_)
    assert actual.gas_limit == eth_tester_provider.max_gas


def test_internal_tx(arbitrum):
    tx = arbitrum.create_transaction(type=INTERNAL_TRANSACTION_TYPE, gas_limit=10000)
    assert tx.type == INTERNAL_TRANSACTION_TYPE


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
