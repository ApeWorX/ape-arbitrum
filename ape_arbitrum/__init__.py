from ape import plugins
from ape.api import NetworkAPI, create_network_type
from ape.api.networks import LOCAL_NETWORK_NAME
from ape_geth import GethProvider
from ape_test import LocalProvider

from .ecosystem import NETWORKS, Arbitrum, ArbitrumConfig


@plugins.register(plugins.Config)
def config_class():
    return ArbitrumConfig


@plugins.register(plugins.EcosystemPlugin)
def ecosystems():
    yield Arbitrum


@plugins.register(plugins.NetworkPlugin)
def networks():
    for network_name, network_params in NETWORKS.items():
        yield "arbitrum", network_name, create_network_type(*network_params)

    # NOTE: This works for development providers, as they get chain_id from themselves
    yield "arbitrum", LOCAL_NETWORK_NAME, NetworkAPI
    yield "arbitrum", "arbitrum-fork", NetworkAPI


@plugins.register(plugins.ProviderPlugin)
def providers():
    for network_name in NETWORKS:
        yield "arbitrum", network_name, GethProvider

    yield "arbitrum", LOCAL_NETWORK_NAME, LocalProvider
