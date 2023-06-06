def test_gas_limit(networks):
    arbitrum = networks.arbitrum
    assert arbitrum.config.local.gas_limit == "max"
