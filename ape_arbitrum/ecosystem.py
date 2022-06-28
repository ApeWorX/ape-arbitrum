from ape.api.config import PluginConfig
from ape.api.networks import LOCAL_NETWORK_NAME
from ape_ethereum.ecosystem import Ethereum, NetworkConfig
from ape.api import TransactionAPI
from eth_utils import (
    add_0x_prefix,
    decode_hex,
)
from eth_typing import HexStr
from ape_ethereum.transactions import (
    StaticFeeTransaction,
    TransactionType,
)
from ape.types import TransactionSignature

NETWORKS = {
    # chain_id, network_id
    "mainnet": (42161, 42161),
    "testnet": (421611, 421611),
}


class ArbitrumConfig(PluginConfig):
    mainnet: NetworkConfig = NetworkConfig(required_confirmations=1, block_time=1)  # type: ignore
    local: NetworkConfig = NetworkConfig(default_provider="test")  # type: ignore
    default_network: str = "mainnet"


class Arbitrum(Ethereum):
    @property
    def config(self) -> ArbitrumConfig:  # type: ignore
        return self.config_manager.get_config("arbitrum")  # type: ignore

    def create_transaction(self, **kwargs) -> TransactionAPI:
        """
        Returns a transaction using the given constructor kwargs.
        Returns:
            :class:`~ape.api.transactions.TransactionAPI`
        """

        transaction_types = {
            TransactionType.STATIC: StaticFeeTransaction,
        }

        if "type" in kwargs:
            type_kwarg = kwargs["type"]
            if type_kwarg is None:
                type_kwarg = TransactionType.STATIC.value
            elif isinstance(type_kwarg, int):
                type_kwarg = f"0{type_kwarg}"
            elif isinstance(type_kwarg, bytes):
                type_kwarg = type_kwarg.hex()

            suffix = type_kwarg.replace("0x", "")
            if len(suffix) == 1:
                type_kwarg = f"{type_kwarg.rstrip(suffix)}0{suffix}"

            version_str = add_0x_prefix(HexStr(type_kwarg))
            version = TransactionType(version_str)
        else:
            version = TransactionType.STATIC

        txn_class = transaction_types[version]
        kwargs["type"] = version.value

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

        return txn_class(**kwargs)  # type: ignore
