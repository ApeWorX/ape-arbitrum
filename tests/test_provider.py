def test_basic(account, second_account, networks, eth_tester_provider):
    receipt = account.transfer(second_account, 100)

    assert not receipt.failed
    assert receipt.value == 100


def test_get_receipt(account, second_account, networks, eth_tester_provider):
    transfer = account.transfer(second_account, 1)
    assert transfer.txn_hash
    tx = networks.provider.get_receipt(transfer.txn_hash)
    assert tx.data.hex()
