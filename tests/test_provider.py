def test_basic(accounts, networks):
    with networks.arbitrum.local.use_provider("test"):
        a = accounts.test_accounts[0]
        receipt = a.transfer(a, 100)

        assert not receipt.failed
        assert receipt.value == 100


def test_receipt(accounts, networks):
    with networks.arbitrum.local.use_provider("test"):
        transfer = accounts.test_accounts[0].transfer(accounts.test_accounts[1], 1)
        assert transfer.txn_hash
        tx = networks.provider.get_receipt(transfer.txn_hash)
        assert tx.data.hex()
