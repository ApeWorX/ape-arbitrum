from ape_arbitrum.ecosystem import LOCAL_GAS_LIMIT, ArbitrumConfig
from ape_ethereum.transactions import TransactionType


def test_gas_limit(arbitrum):
    # NOTE: The reason we have a hard-coded gas limit is because
    #   the block gas limit in Arbitrum is extremely high.
    assert arbitrum.config.local.gas_limit == LOCAL_GAS_LIMIT


def test_default_transaction_type(arbitrum):
    assert arbitrum.config.mainnet.default_transaction_type == TransactionType.DYNAMIC


def test_mainnet_fork_not_configured():
    obj = ArbitrumConfig.model_validate({})
    assert obj.mainnet_fork.required_confirmations == 0


def test_mainnet_fork_configured():
    data = {"mainnet_fork": {"required_confirmations": 555}}
    obj = ArbitrumConfig.model_validate(data)
    assert obj.mainnet_fork.required_confirmations == 555


def test_custom_network():
    data = {"apenet": {"required_confirmations": 333}}
    obj = ArbitrumConfig.model_validate(data)
    assert obj.apenet.required_confirmations == 333
