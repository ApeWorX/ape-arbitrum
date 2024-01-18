import time
from typing import Dict, Optional, Type, cast

from ape.api.config import PluginConfig
from ape.api.networks import LOCAL_NETWORK_NAME
from ape.api.transactions import ConfirmationsProgressBar, ReceiptAPI, TransactionAPI
from ape.exceptions import ApeException, TransactionError
from ape.logging import logger
from ape.types import TransactionSignature
from ape.utils import DEFAULT_LOCAL_TRANSACTION_ACCEPTANCE_TIMEOUT
from ape_ethereum.ecosystem import Ethereum, ForkedNetworkConfig, NetworkConfig
from ape_ethereum.transactions import (
    DynamicFeeTransaction,
    Receipt,
    AccessListTransaction,
    StaticFeeTransaction,
    TransactionStatusEnum,
)
from ape_ethereum.transactions import TransactionType as EthTransactionType
from eth_pydantic_types import HexBytes
from pydantic.fields import Field

NETWORKS = {
    # chain_id, network_id
    "mainnet": (42161, 42161),
    "goerli": (421613, 421613),
    "sepolia": (421614, 421614),
}
INTERNAL_TRANSACTION_TYPE = 106

# NOTE: Use a hard-coded gas limit for testing
#   because the block gasLimit is extremely high in Arbitrum networks.
LOCAL_GAS_LIMIT = 30_000_000


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


def _create_config(
    required_confirmations: int = 1,
    block_time: int = 1,
    cls: Type = NetworkConfig,
    **kwargs,
) -> NetworkConfig:
    return cls(
        required_confirmations=required_confirmations,
        block_time=block_time,
        default_transaction_type=EthTransactionType.STATIC,
        **kwargs,
    )


def _create_local_config(default_provider: Optional[str] = None, use_fork: bool = False, **kwargs):
    return _create_config(
        block_time=0,
        default_provider=default_provider,
        gas_limit=LOCAL_GAS_LIMIT,
        required_confirmations=0,
        transaction_acceptance_timeout=DEFAULT_LOCAL_TRANSACTION_ACCEPTANCE_TIMEOUT,
        cls=ForkedNetworkConfig if use_fork else NetworkConfig,
        **kwargs,
    )


class ArbitrumConfig(PluginConfig):
    mainnet: NetworkConfig = _create_config()
    mainnet_fork: ForkedNetworkConfig = _create_local_config(use_fork=True)
    goerli: NetworkConfig = _create_config()
    goerli_fork: ForkedNetworkConfig = _create_local_config(use_fork=True)
    sepolia: NetworkConfig = _create_config()
    sepolia_fork: ForkedNetworkConfig = _create_local_config(use_fork=True)
    local: NetworkConfig = _create_local_config(default_provider="test")
    default_network: str = LOCAL_NETWORK_NAME


class Arbitrum(Ethereum):
    @property
    def config(self) -> ArbitrumConfig:  # type: ignore[override]
        return cast(ArbitrumConfig, self.config_manager.get_config("arbitrum"))

    def create_transaction(self, **kwargs) -> TransactionAPI:
        """
        Returns a transaction using the given constructor kwargs.
        Overridden because does not support

        **kwargs: Kwargs for the transaction class.

        Returns:
            :class:`~ape.api.transactions.TransactionAPI`
        """


        # Handle all aliases.
        tx_data = dict(kwargs)
        tx_data = _correct_key(
            "max_priority_fee",
            tx_data,
            ("max_priority_fee_per_gas", "maxPriorityFeePerGas", "maxPriorityFee"),
        )
        tx_data = _correct_key("max_fee", tx_data, ("max_fee_per_gas", "maxFeePerGas", "maxFee"))
        tx_data = _correct_key("gas", tx_data, ("gas_limit", "gasLimit"))
        tx_data = _correct_key("gas_price", tx_data, ("gasPrice",))
        tx_data = _correct_key(
            "type",
            tx_data,
            ("txType", "tx_type", "txnType", "txn_type", "transactionType", "transaction_type"),
        )

        # Handle unique value specifications, such as "1 ether".
        if "value" in tx_data and not isinstance(tx_data["value"], int):
            value = tx_data["value"] or 0  # Convert None to 0.
            tx_data["value"] = self.conversion_manager.convert(value, int)

        # None is not allowed, the user likely means `b""`.
        if "data" in tx_data and tx_data["data"] is None:
            tx_data["data"] = b""

        # Deduce the transaction type.
        transaction_types: Dict[int, Type[TransactionAPI]] = {
            EthTransactionType.STATIC.value: StaticFeeTransaction,
            EthTransactionType.DYNAMIC.value: DynamicFeeTransaction,
            EthTransactionType.ACCESS_LIST.value: AccessListTransaction,
            INTERNAL_TRANSACTION_TYPE: InternalTransaction,
        }

        if "type" in tx_data:
            if tx_data["type"] is None:
                # Explicit `None` means used default.
                version = self.default_transaction_type
            elif isinstance(tx_data["type"], EthTransactionType):
                version = tx_data["type"]
            elif isinstance(tx_data["type"], int):
                version = TransactionType(tx_data["type"])
            else:
                # Using hex values or alike.
                version = TransactionType(self.conversion_manager.convert(tx_data["type"], int))

        elif "gas_price" in tx_data:
            version = TransactionType.STATIC
        elif "max_fee" in tx_data or "max_priority_fee" in tx_data:
            version = TransactionType.DYNAMIC
        elif "access_list" in tx_data or "accessList" in tx_data:
            version = TransactionType.ACCESS_LIST
        else:
            version = self.default_transaction_type

        tx_data["type"] = version.value

        # This causes problems in pydantic for some reason.
        # NOTE: This must happen after deducing the tx type!
        if "gas_price" in tx_data and tx_data["gas_price"] is None:
            del tx_data["gas_price"]

        txn_class = transaction_types[version]

        if "required_confirmations" not in tx_data or tx_data["required_confirmations"] is None:
            # Attempt to use default required-confirmations from `ape-config.yaml`.
            required_confirmations = 0
            active_provider = self.network_manager.active_provider
            if active_provider:
                required_confirmations = active_provider.network.required_confirmations

            tx_data["required_confirmations"] = required_confirmations

        if isinstance(tx_data.get("chainId"), str):
            tx_data["chainId"] = int(tx_data["chainId"], 16)

        elif (
            "chainId" not in tx_data or tx_data["chainId"] is None
        ) and self.network_manager.active_provider is not None:
            tx_data["chainId"] = self.provider.chain_id

        if "input" in tx_data:
            tx_data["data"] = tx_data.pop("input")

        if all(field in tx_data for field in ("v", "r", "s")):
            tx_data["signature"] = TransactionSignature(
                v=tx_data["v"],
                r=bytes(tx_data["r"]),
                s=bytes(tx_data["s"]),
            )

        if "gas" not in tx_data:
            tx_data["gas"] = None

        return txn_class(**tx_data)

        # transaction_types: Dict[int, Type[TransactionAPI]] = {
        #     EthTransactionType.STATIC.value: StaticFeeTransaction,
        #     EthTransactionType.DYNAMIC.value: DynamicFeeTransaction,
        #     INTERNAL_TRANSACTION_TYPE: InternalTransaction,
        # }
        #
        # if "type" in kwargs:
        #     if kwargs["type"] is None:
        #         # The Default is pre-EIP-1559.
        #         version = self.default_transaction_type.value
        #     elif not isinstance(kwargs["type"], int):
        #         version = self.conversion_manager.convert(kwargs["type"], int)
        #     else:
        #         version = kwargs["type"]
        #
        # elif "gas_price" in kwargs:
        #     version = EthTransactionType.STATIC.value
        # else:
        #     version = self.default_transaction_type.value
        #
        # kwargs["type"] = version
        # txn_class = transaction_types[version]
        #
        # if "required_confirmations" not in kwargs or kwargs["required_confirmations"] is None:
        #     # Attempt to use default required-confirmations from `ape-config.yaml`.
        #     required_confirmations = 0
        #     active_provider = self.network_manager.active_provider
        #     if active_provider:
        #         required_confirmations = active_provider.network.required_confirmations
        #
        #     kwargs["required_confirmations"] = required_confirmations
        #
        # if isinstance(kwargs.get("chainId"), str):
        #     kwargs["chainId"] = int(kwargs["chainId"], 16)
        #
        # elif "chainId" not in kwargs and self.network_manager.active_provider is not None:
        #     kwargs["chainId"] = self.provider.chain_id
        #
        # if "input" in kwargs:
        #     kwargs["data"] = kwargs.pop("input")
        #
        # if all(field in kwargs for field in ("v", "r", "s")):
        #     kwargs["signature"] = TransactionSignature(
        #         v=kwargs["v"],
        #         r=bytes(kwargs["r"]),
        #         s=bytes(kwargs["s"]),
        #     )
        #
        # if "max_priority_fee_per_gas" in kwargs:
        #     kwargs["max_priority_fee"] = kwargs.pop("max_priority_fee_per_gas")
        # if "max_fee_per_gas" in kwargs:
        #     kwargs["max_fee"] = kwargs.pop("max_fee_per_gas")
        #
        # kwargs["gas"] = kwargs.pop("gas_limit", kwargs.get("gas"))
        #
        # if "value" in kwargs and not isinstance(kwargs["value"], int):
        #     kwargs["value"] = self.conversion_manager.convert(kwargs["value"], int)
        #
        # return txn_class(**kwargs)

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

        block_number = data.get("block_number") or data.get("blockNumber")
        if block_number is None:
            raise ValueError("Block number cannot be None")

        return ArbitrumReceipt(
            block_number=block_number,
            contract_address=data.get("contract_address") or data.get("contractAddress"),
            gas_limit=data.get("gas", data.get("gas_limit", data.get("gasLimit"))) or 0,
            gas_price=data.get("gas_price", data.get("gasPrice")) or 0,
            gas_used=data.get("gas_used", data.get("gasUsed")) or 0,
            logs=data.get("logs", []),
            status=status,
            txn_hash=txn_hash,
            transaction=self.create_transaction(**data),
        )
