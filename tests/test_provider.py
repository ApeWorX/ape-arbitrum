def test_basic(accounts, networks):
    with networks.arbitrum.local.use_provider("test"):
        a = accounts.test_accounts[0]
        receipt = a.transfer(a, 100)

        assert not receipt.failed
        assert receipt.value == 100


def test_receipt(accounts, networks):
    with networks.arbitrum.mainnet.use_provider("alchemy"):
        tx = networks.provider.get_receipt(
            "0x1c38688523bf47921fef5551451fefa6e2e5d77991ea674d572f02d72dda4dc7"
        )
        assert tx
