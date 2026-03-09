---
name: ave-data-wss
version: 2.0.0
description: |
  Stream real-time on-chain data via the AVE Cloud WebSocket API (wss://wss.ave-api.xyz).
  Use this skill whenever the user wants to:
  - Stream live swap or liquidity events for a trading pair in real time
  - Monitor live kline/candlestick updates for a trading pair
  - Subscribe to live price change notifications for one or more tokens
  - Run an interactive WebSocket REPL to manage subscriptions live
  - Start or stop the Ave Cloud server daemon (Docker-based persistent connection)

  Requires API_PLAN=pro for all WebSocket streams.

  DO NOT use this skill for:
  - REST data queries (token search, price, kline history, holders, etc.) → use ave-data-rest instead
  - Executing trades or swaps → use ave-trade-chain-wallet or ave-trade-proxy-wallet instead
license: MIT
metadata:
  openclaw:
    primaryEnv: AVE_API_KEY
    requires:
      env:
        - AVE_API_KEY
        - API_PLAN
      bins:
        - python3
        - docker
---

# ave-data-wss

Real-time on-chain data streams via the AVE Cloud WebSocket API. Requires `API_PLAN=pro`.

## Setup

```bash
export AVE_API_KEY="your_api_key_here"
export API_PLAN="pro"
pip install -r scripts/requirements.txt
```

Or use Docker (recommended for server/daemon mode):

```bash
docker build -f scripts/Dockerfile.txt -t ave-cloud .
```

## Operations

### Interactive REPL (recommended for live monitoring)

```bash
# Docker
docker run -it -e AVE_API_KEY="your_key" -e API_PLAN=pro ave-cloud wss-repl

# Local
python scripts/ave_data_wss.py wss-repl
```

At the `>` prompt:

| Command | Description |
|---------|-------------|
| `subscribe price <addr-chain> [...]` | Live price updates for one or more tokens |
| `subscribe tx <pair> <chain> [tx\|multi_tx\|liq]` | Swap or liquidity events for a pair |
| `subscribe kline <pair> <chain> [interval]` | Kline candle updates for a pair |
| `unsubscribe` | Cancel current subscription |
| `quit` | Close connection and exit |

JSON events stream to stdout; UI messages go to stderr (safe to pipe to `jq`).

### Stream live swap/liquidity events

```bash
python scripts/ave_data_wss.py watch-tx --address <pair_address> --chain <chain> [--topic tx]
```

`--topic` choices: `tx` (default), `multi_tx`, `liq`

### Stream live kline updates

```bash
python scripts/ave_data_wss.py watch-kline --address <pair_address> --chain <chain> [--interval k60]
```

`--interval` choices: `s1 k1 k5 k15 k30 k60 k120 k240 k1440 k10080`

### Stream live price changes

```bash
python scripts/ave_data_wss.py watch-price --tokens <addr1>-<chain1> [<addr2>-<chain2> ...]
```

### Server daemon (Docker)

```bash
python scripts/ave_data_wss.py start-server   # start background Docker container
python scripts/ave_data_wss.py stop-server    # stop it
python scripts/ave_data_wss.py serve          # run in foreground (used as Docker entrypoint)
```

## Reference

See `references/data-api-doc.md` for full WebSocket API reference.
