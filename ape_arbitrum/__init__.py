from ape import plugins


@plugins.register(plugins.Config)
def config_class():
    from .ecosystem import ArbitrumConfig

    return ArbitrumConfig


@plugins.register(plugins.EcosystemPlugin)
def ecosystems():
    from .ecosystem import Arbitrum

    yield Arbitrum


@plugins.register(plugins.NetworkPlugin)
def networks():
    from ape.api.networks import (
        LOCAL_NETWORK_NAME,
        ForkedNetworkAPI,
        NetworkAPI,
        create_network_type,
    )

    from .ecosystem import NETWORKS

    for network_name, network_params in NETWORKS.items():
        yield "arbitrum", network_name, create_network_type(*network_params)
        yield "arbitrum", f"{network_name}-fork", ForkedNetworkAPI

    # NOTE: This works for development providers, as they get chain_id from themselves
    yield "arbitrum", LOCAL_NETWORK_NAME, NetworkAPI


@plugins.register(plugins.ProviderPlugin)
def providers():
    from ape.api.networks import LOCAL_NETWORK_NAME
    from ape_node import Node
    from ape_test import LocalProvider

    from .ecosystem import NETWORKS

    for network_name in NETWORKS:
        yield "arbitrum", network_name, Node

    yield "arbitrum", LOCAL_NETWORK_NAME, LocalProvider


def __getattr__(name: str):
    import ape_arbitrum.ecosystem as module

    return getattr(module, name)


__all__ = [
    "NETWORKS",
    "Arbitrum",
    "ArbitrumConfig",
]
