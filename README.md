# Ape Arbitrum Ecosystem Plugin

Ecosystem Plugin for Arbitrum support in Ape

## Dependencies

* [python3](https://www.python.org/downloads) version 3.7.2 or greater, python3-dev

## Installation

### via `ape`

You can install this plugin using `ape`:

```bash
ape plugins install arbitrum
```

or via config file:

```yaml
# ape-config.yaml
plugins:
  - name: arbitrum
```

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install ape-arbitrum
```

### via `setuptools`

You can clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
git clone https://github.com/ApeWorX/ape-arbitrum.git
cd ape-arbitrum
python3 setup.py install
```

## Quick Usage

Installing this plugin adds support for the Arbitrum ecosystem:

```bash
ape console --network arbitrum:mainnet
```

## Alchemy

To use Alchemy with ape-arbitrum you have to install the [Arbitrum fork of the ape-alchemy plugin](https://github.com/Jam516/ape-alchemy/tree/feat/kofi/add-arbitrum).

```bash
ape console --network arbitrum:mainnet:alchemy
```

## Development

Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [Apache 2.0](LICENSE).
