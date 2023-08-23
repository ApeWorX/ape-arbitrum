import time
from typing import Optional, Type, cast

from ape.api.config import PluginConfig
from ape.api.networks import LOCAL_NETWORK_NAME
from ape.api.transactions import ConfirmationsProgressBar, ReceiptAPI, TransactionAPI
from ape.exceptions import ApeException, TransactionError
from ape.logging import logger
from ape.types import TransactionSignature
from ape.utils import DEFAULT_LOCAL_TRANSACTION_ACCEPTANCE_TIMEOUT, to_int
from ape_ethereum.ecosystem import Ethereum, NetworkConfig
from ape_ethereum.transactions import (
    DynamicFeeTransaction,
    Receipt,
    StaticFeeTransaction,
    TransactionStatusEnum,
)
from ape_ethereum.transactions import TransactionType as EthTransactionType
from eth_utils import decode_hex
from ethpm_types import HexBytes
from pydantic.fields import Field

NETWORKS = {
    # chain_id, network_id
    "mainnet": (42161, 42161),
    "goerli": (421613, 421613),
}
INTERNAL_TRANSACTION_TYPE = 106


class InternalTransaction(StaticFeeTransaction):
    type: int = Field(INTERNAL_TRANSACTION_TYPE, exclude=True)


class ApeArbitrumError(ApeException):
    """
    Raised in the ape-arbitrum plugin.
    """


class ArbitrumReceipt(Receipt):
    def await_confirmations(self) -> "ReceiptAPI":
        """
        Overridden to handle skipping nonce-check for internal txns.
        """

        if self.type != INTERNAL_TRANSACTION_TYPE:
            return super().await_confirmations()

        # This logic is copied from ape-ethereum but removes the nonce-increase
        # waiting, as internal transactions don't increase a nonce (apparently).

        try:
            self.raise_for_status()
        except TransactionError:
            # Skip waiting for confirmations when the transaction has failed.
            return self

        if self.required_confirmations == 0:
            # The transaction might not yet be confirmed but
            # the user is aware of this. Or, this is a development environment.
            return self

        confirmations_occurred = self._confirmations_occurred
        if self.required_confirmations and confirmations_occurred >= self.required_confirmations:
            return self

        # If we get here, that means the transaction has been recently submitted.
        if explorer_url := self._explorer and self._explorer.get_transaction_url(self.txn_hash):
            log_message = f"Submitted {explorer_url}"
        else:
            log_message = f"Submitted {self.txn_hash}"

        logger.info(log_message)

        if self.required_confirmations:
            with ConfirmationsProgressBar(self.required_confirmations) as progress_bar:
                while confirmations_occurred < self.required_confirmations:
                    confirmations_occurred = self._confirmations_occurred
                    progress_bar.confs = confirmations_occurred

                    if confirmations_occurred == self.required_confirmations:
                        break

                    time_to_sleep = int(self._block_time / 2)
                    time.sleep(time_to_sleep)

        return self


def _create_network_config(
    required_confirmations: int = 1, block_time: int = 1, **kwargs
) -> NetworkConfig:
    return NetworkConfig(
        required_confirmations=required_confirmations, block_time=block_time, **kwargs
    )


def _create_local_config(default_provider: Optional[str] = None, **kwargs) -> NetworkConfig:
    return _create_network_config(
        required_confirmations=0,
        default_provider=default_provider,
        transaction_acceptance_timeout=DEFAULT_LOCAL_TRANSACTION_ACCEPTANCE_TIMEOUT,
        gas_limit="max",
        **kwargs,
    )


class ArbitrumConfig(PluginConfig):
    mainnet: NetworkConfig = _create_network_config()
    mainnet_fork: NetworkConfig = _create_local_config()
    goerli: NetworkConfig = _create_network_config()
    goerli_fork: NetworkConfig = _create_local_config()
    local: NetworkConfig = _create_local_config(default_provider="test")
    default_network: str = LOCAL_NETWORK_NAME


class Arbitrum(Ethereum):
    @property
    def config(self) -> ArbitrumConfig:  # type: ignore
        return cast(ArbitrumConfig, self.config_manager.get_config("arbitrum"))

    def create_transaction(self, **kwargs) -> TransactionAPI:
        """
        Returns a transaction using the given constructor kwargs.
        Overridden because does not support

        **kwargs: Kwargs for the transaction class.

        Returns:
            :class:`~ape.api.transactions.TransactionAPI`
        """

        transaction_type = to_int(kwargs.get("type", EthTransactionType.STATIC.value))
        kwargs["type"] = transaction_type
        txn_class = _get_transaction_cls(transaction_type)

        if "required_confirmations" not in kwargs or kwargs["required_confirmations"] is None:
            # Attempt to use default required-confirmations from `ape-config.yaml`.
            required_confirmations = 0
            active_provider = self.network_manager.active_provider
            if active_provider:
                required_confirmations = active_provider.network.required_confirmations

            kwargs["required_confirmations"] = required_confirmations

        if isinstance(kwargs.get("chainId"), str):
            kwargs["chainId"] = int(kwargs["chainId"], 16)

        if "input" in kwargs:
            kwargs["data"] = decode_hex(kwargs.pop("input").hex())

        if all(field in kwargs for field in ("v", "r", "s")):
            kwargs["signature"] = TransactionSignature(  # type: ignore
                v=kwargs["v"],
                r=bytes(kwargs["r"]),
                s=bytes(kwargs["s"]),
            )

        return txn_class.parse_obj(kwargs)

    def decode_receipt(self, data: dict) -> ReceiptAPI:
        """
        NOTE: Overridden to use custom receipt class.
        """
        status = data.get("status")
        if status:
            status = self.conversion_manager.convert(status, int)
            status = TransactionStatusEnum(status)

        txn_hash = None
        hash_key_choices = ("hash", "txHash", "txnHash", "transactionHash", "transaction_hash")
        for choice in hash_key_choices:
            if choice in data:
                txn_hash = data[choice]
                break

        if txn_hash:
            txn_hash = txn_hash.hex() if isinstance(txn_hash, HexBytes) else txn_hash

        data_bytes = data.get("data", b"")
        if data_bytes and isinstance(data_bytes, str):
            data["data"] = HexBytes(data_bytes)

        elif "input" in data and isinstance(data["input"], str):
            data["input"] = HexBytes(data["input"])

        receipt = ArbitrumReceipt(
            block_number=data.get("block_number") or data.get("blockNumber"),
            contract_address=data.get("contract_address") or data.get("contractAddress"),
            gas_limit=data.get("gas", data.get("gas_limit", data.get("gasLimit"))) or 0,
            gas_price=data.get("gas_price", data.get("gasPrice")) or 0,
            gas_used=data.get("gas_used", data.get("gasUsed")) or 0,
            logs=data.get("logs", []),
            status=status,
            txn_hash=txn_hash,
            transaction=self.create_transaction(**data),
        )
        return receipt


def _get_transaction_cls(transaction_type: int) -> Type[TransactionAPI]:
    transaction_types = {
        EthTransactionType.STATIC.value: StaticFeeTransaction,
        EthTransactionType.DYNAMIC.value: DynamicFeeTransaction,
        INTERNAL_TRANSACTION_TYPE: InternalTransaction,
    }
    if transaction_type not in transaction_types:
        raise ApeArbitrumError(f"Transaction type '{transaction_type}' not supported.")

    return transaction_types[transaction_type]
