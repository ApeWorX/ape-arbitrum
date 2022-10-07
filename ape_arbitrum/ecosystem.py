from typing import Optional, Type, Union, cast

from ape.api import TransactionAPI
from ape.api.config import PluginConfig
from ape.api.networks import LOCAL_NETWORK_NAME
from ape.exceptions import ApeException
from ape.types import TransactionSignature
from ape_ethereum.ecosystem import Ethereum, NetworkConfig
from ape_ethereum.transactions import StaticFeeTransaction, TransactionType
from eth_typing import HexStr
from eth_utils import add_0x_prefix, decode_hex

NETWORKS = {
    # chain_id, network_id
    "mainnet": (42161, 42161),
    "goerli": (421613, 421613),
}


class ApeArbitrumError(ApeException):
    """
    Raised in the ape-arbitrum plugin.
    """


class ArbitrumConfig(PluginConfig):
    mainnet: NetworkConfig = NetworkConfig(required_confirmations=1, block_time=1)  # type: ignore
    local: NetworkConfig = NetworkConfig(default_provider="test")  # type: ignore
    default_network: str = LOCAL_NETWORK_NAME


class Arbitrum(Ethereum):
    @property
    def config(self) -> ArbitrumConfig:  # type: ignore
        return cast(ArbitrumConfig, self.config_manager.get_config("arbitrum"))

    def create_transaction(self, **kwargs) -> TransactionAPI:
        """
        Returns a transaction using the given constructor kwargs.
        Returns:
            :class:`~ape.api.transactions.TransactionAPI`
        """

        transaction_type = _get_transaction_type(kwargs.get("type"))
        kwargs["type"] = transaction_type.value
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
            kwargs["data"] = decode_hex(kwargs.pop("input"))

        if all(field in kwargs for field in ("v", "r", "s")):
            kwargs["signature"] = TransactionSignature(  # type: ignore
                v=kwargs["v"],
                r=bytes(kwargs["r"]),
                s=bytes(kwargs["s"]),
            )

        return txn_class.parse_obj(kwargs)


def _get_transaction_type(_type: Optional[Union[int, str, bytes]]) -> TransactionType:
    if not _type:
        return TransactionType.STATIC

    if _type is None:
        _type = TransactionType.STATIC.value
    elif isinstance(_type, int):
        _type = f"0{_type}"
    elif isinstance(_type, bytes):
        _type = _type.hex()

    suffix = _type.replace("0x", "")
    if len(suffix) == 1:
        _type = f"{_type.rstrip(suffix)}0{suffix}"

    return TransactionType(add_0x_prefix(HexStr(_type)))


def _get_transaction_cls(transaction_type: TransactionType) -> Type[TransactionAPI]:
    transaction_types = {
        TransactionType.STATIC: StaticFeeTransaction,
    }
    if transaction_type not in transaction_types:
        raise ApeArbitrumError(f"Transaction type '{transaction_type}' not supported.")

    return transaction_types[transaction_type]
