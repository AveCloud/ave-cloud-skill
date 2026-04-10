# AVE Cloud Skills

[![Promptfoo Code Scan](https://github.com/AveCloud/ave-cloud-skill/actions/workflows/promptfoo-code-scan.yml/badge.svg)](https://github.com/AveCloud/ave-cloud-skill/actions/workflows/promptfoo-code-scan.yml)

[English](README.md) | [中文](README.zh-CN.md)

[Website](https://cloud.ave.ai/) | [X](https://x.com/AveaiGlobal) | [Telegram](https://t.me/ave_ai_cloud)

Ave Cloud skill suite for querying on-chain crypto data and executing DEX trades via the Ave Cloud API (https://cloud.ave.ai). Supports BSC, Solana, ETH, and Base.

## Why AVE Cloud Skills

- Real-time multi-chain data (BSC, Solana, ETH, Base)
- Self-custody chain-wallet and server-managed proxy-wallet trading
- Live WebSocket streams for price, transaction, and kline data
- Built-in risk and honeypot safety checks

## Skills

| Skill | Script | When to Use |
|---|---|---|
| ave-data-rest | ave_data_rest.py | Token search, price, kline, holders, swap txs, trending, risk |
| ave-data-wss | ave_data_wss.py | Real-time price/tx/kline streams, WSS REPL, server daemon (requires API_PLAN=pro) |
| ave-trade-chain-wallet | ave_trade_rest.py | Self-custody DEX trades, user controls private keys |
| ave-trade-proxy-wallet | ave_trade_rest.py, ave_trade_wss.py | Market/limit orders, TP/SL, proxy wallet management (requires API_PLAN=normal or pro) |
| ave-wallet-suite | (router) | Routes ambiguous wallet/trade/data requests to the correct sub-skill |

## Quick Start

Build the local Docker image first:

```bash
docker build -f scripts/Dockerfile.txt -t ave-cloud .
```

### Token Search

```bash
docker run --rm \
  -e AVE_API_KEY=your_api_key_here \
  -e API_PLAN=free \
  --entrypoint python3 \
  ave-cloud scripts/ave_data_rest.py search --keyword PEPE
```

### Live Watch

```bash
docker run --rm -it \
  -e AVE_API_KEY=your_api_key_here \
  -e API_PLAN=pro \
  --entrypoint python3 \
  ave-cloud scripts/ave_data_wss.py wss-repl
```

### Dry-Run Trade Preview

```bash
docker run --rm \
  -e AVE_API_KEY=your_api_key_here \
  -e API_PLAN=free \
  --entrypoint python3 \
  ave-cloud scripts/ave_trade_rest.py quote \
  --chain bsc \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 \
  --swap-type buy
```

## Installation

### Install Matrix

| Client | Method | Config Dir |
|---|---|---|
| Claude Code | plugin discovery | .claude-plugin/ |
| Codex | clone + symlink | .codex/ |
| Cursor | plugin discovery | .cursor-plugin/ |
| OpenCode | clone + symlink | .opencode/ |
| OpenClaw | clone + symlink | .openclaw/ |

See each config directory for client-specific install instructions.

### API Plan Matrix

| Feature | free | normal | pro |
|---|---|---|---|
| Data REST | Yes | Yes | Yes |
| Data WSS | No | No | Yes |
| Trade Chain-Wallet | Yes | Yes | Yes |
| Trade Proxy-Wallet | No | Yes | Yes |

Get your API key at https://cloud.ave.ai

## Supported Chains

Data REST and Data WSS cover more chains, but the full trading flow in this repo focuses on the four chains below.

| Chain | Data | Chain-Wallet | Proxy-Wallet |
|---|---|---|---|
| BSC | Yes | Yes | Yes |
| Solana | Yes | Yes | Yes |
| ETH | Yes | Yes | Yes |
| Base | Yes | Yes | Yes |

## Environment Variables

| Variable | Required by | Description |
|---|---|---|
| AVE_API_KEY | all skills | Ave Cloud API key from https://cloud.ave.ai |
| API_PLAN | all skills | free / normal / pro |
| AVE_SECRET_KEY | trade-proxy-wallet | HMAC signing secret for proxy wallet auth |
| AVE_EVM_PRIVATE_KEY | trade-chain-wallet (optional) | Hex private key for BSC/ETH/Base signing |
| AVE_SOLANA_PRIVATE_KEY | trade-chain-wallet (optional) | Base58 private key for Solana signing |
| AVE_MNEMONIC | trade-chain-wallet (optional) | BIP39 mnemonic for all chains |
| AVE_USE_DOCKER | all scripts | Set to true for Docker-backed execution and Docker rate limiting |
| AVE_BSC_RPC_URL | trade-chain-wallet (optional) | Override BSC JSON-RPC URL |
| AVE_ETH_RPC_URL | trade-chain-wallet (optional) | Override ETH JSON-RPC URL |
| AVE_BASE_RPC_URL | trade-chain-wallet (optional) | Override Base JSON-RPC URL |

## Token Links

View token details on AVE Pro: `https://pro.ave.ai/token/<token>-<chain>`

Example: `https://pro.ave.ai/token/0x1234...abcd-bsc`

## License

MIT
