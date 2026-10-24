# Quick Start

Ecosystem Plugin for Arbitrum support in Ape.

## Dependencies

- [Python 3](https://www.python.org/downloads) version 3.10 or greater.

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

### via source

You can clone the repository and install for development:

```bash
git clone https://github.com/ApeWorX/ape-arbitrum.git
cd ape-arbitrum
uv sync --group dev
uv run prek install
```

## Quick Usage

Installing this plugin adds support for the Arbitrum ecosystem:

```bash
ape console --network arbitrum:mainnet
```

## Development

This project is in development and should be considered a beta.
Things might not be in their final state and breaking changes may occur.
Comments, questions, criticisms and pull requests are welcomed.
