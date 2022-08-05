def test_basic(accounts, networks):

    with networks.arbitrum.local.use_provider("test"):
        a = accounts.test_accounts[0]
        receipt = a.transfer(a, 100)

        assert not receipt.failed
        assert receipt.value == 100
