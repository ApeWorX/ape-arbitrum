from ape.api.config import PluginConfig
from ape.api.networks import LOCAL_NETWORK_NAME
from ape_ethereum.ecosystem import Ethereum, NetworkConfig

NETWORKS = {
    # chain_id, network_id
    "mainnet": (42161, 42161),
    "testnet": (421611, 421611),
}


class ArbitrumConfig(PluginConfig):
    mainnet: NetworkConfig = NetworkConfig(required_confirmations=1, block_time=1)  # type: ignore
    local: NetworkConfig = NetworkConfig(default_provider="test")  # type: ignore
    default_network: str = LOCAL_NETWORK_NAME


class Arbitrum(Ethereum):
    @property
    def config(self) -> ArbitrumConfig:  # type: ignore
        return self.config_manager.get_config("arbitrum")  # type: ignore
