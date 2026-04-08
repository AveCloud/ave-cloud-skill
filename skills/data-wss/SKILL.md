---
name: ave-data-wss
version: 2.3.0
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

Live on-chain data streams via the AVE Cloud WebSocket API. For shared connection discipline and response rules, see [operator-playbook.md](../../references/operator-playbook.md).

## Setup

```bash
export AVE_API_KEY="your_api_key_here"
export API_PLAN="pro"
pip install -r scripts/requirements.txt
```

## Rate Limits

All WebSocket streams require `API_PLAN=pro` (20 TPS). Connection discipline matters more than TPS: keep one REPL or server connection open, switch topics with `subscribe` / `unsubscribe`, and avoid stacking parallel sockets unless there is a hard need.

## Supported Chains

All Data REST chains are supported for streaming, including `bsc`, `eth`, `base`, `solana`, `tron`, `polygon`, `arbitrum`.

## Operations

### REPL

Use one interactive connection for multi-topic monitoring.

```bash
python scripts/ave_data_wss.py wss-repl
```

| Command | Description |
|---|---|
| `subscribe price <addr-chain> [...]` | Stream live price changes for one or more tokens |
| `subscribe tx <pair> <chain> [tx|multi_tx|liq]` | Stream swap or liquidity events for a pair |
| `subscribe kline <pair> <chain> [interval]` | Stream live candle updates for a pair |
| `unsubscribe` | Cancel the current subscription |
| `quit` | Close the connection and exit |

### Watch tx

Stream live swap or liquidity events for a pair.

```bash
python scripts/ave_data_wss.py watch-tx --address <pair_address> --chain <chain> [--topic tx]
```

### Watch kline

Stream live kline updates for a pair.

```bash
python scripts/ave_data_wss.py watch-kline --address <pair_address> --chain <chain> [--interval k60] [--format raw|markdown]
```

### Watch price

Stream live price changes for one or more tokens.

```bash
python scripts/ave_data_wss.py watch-price --tokens <addr1>-<chain1> [<addr2>-<chain2> ...]
```

### Server daemon

Start or stop the reusable Docker-backed connection.

```bash
python scripts/ave_data_wss.py start-server
python scripts/ave_data_wss.py stop-server
python scripts/ave_data_wss.py serve
```

## Workflow Example

### Monitor token launch via REPL

Open one connection, watch swaps, then switch to price without opening a second socket.

```bash
python scripts/ave_data_wss.py wss-repl
# at the prompt:
subscribe tx <pair_address> bsc
unsubscribe
subscribe price <token_address>-bsc
quit
```

## Reference

Use shared references for operator rules, recovery patterns, response style, and the full streaming API surface.

- [operator-playbook.md](../../references/operator-playbook.md)
- [error-translation.md](../../references/error-translation.md)
- [response-contract.md](../../references/response-contract.md)
- [presentation-guide.md](../../references/presentation-guide.md)
- [learn-more.md](../../references/learn-more.md)
- [data-api-doc.md](../../references/data-api-doc.md)
