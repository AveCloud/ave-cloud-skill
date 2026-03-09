---
name: ave-data-rest
version: 2.0.0
description: |
  Query on-chain crypto data via the AVE Cloud Data REST API (https://cloud.ave.ai/).
  Use this skill whenever the user wants to:
  - Search for tokens by name, symbol, or contract address
  - Get token price, market cap, TVL, volume, or price change data
  - View kline/candlestick (OHLCV) chart data for a token or trading pair
  - Check top 100 token holders and their distribution
  - Browse recent swap transactions for a trading pair
  - View trending tokens on a specific chain
  - View ranked tokens by topic (hot, meme, gainer, loser, new, AI, DePIN, GameFi, etc.)
  - Run a contract security/risk detection report (honeypot, buy/sell tax, ownership)
  - List supported chain identifiers
  - Get main/native tokens for a chain
  - Get tokens from a specific launchpad or platform (pump.fun, fourmeme, bonk, nadfun)

  DO NOT use this skill for:
  - Real-time streaming or WebSocket subscriptions → use ave-data-wss instead
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
---

# ave-data-rest

Query on-chain token data via the AVE Cloud Data REST API. Covers 130+ blockchains and 300+ DEXs.

## Setup

```bash
export AVE_API_KEY="your_api_key_here"
export API_PLAN="free"   # free | normal | pro
```

Get a free key at https://cloud.ave.ai/register.

Rate limiting is handled by a built-in file-based limiter (stdlib only). Set `AVE_USE_DOCKER=true` to use `requests-ratelimiter` instead (auto-set inside Docker).

## How to use this skill

1. Identify what the user wants from the operations below
2. Run the appropriate command using `scripts/ave_data_rest.py`
3. Format the JSON response as a readable summary or table

All commands output JSON to stdout. Errors go to stderr with a non-zero exit code.

## Operations

### Search tokens

```bash
python scripts/ave_data_rest.py search --keyword <keyword> [--chain <chain>] [--limit 20]
```

### Platform tokens

```bash
python scripts/ave_data_rest.py platform-tokens --platform <platform>
```

Common platforms: `hot`, `new`, `meme`, `pump_in_hot`, `pump_in_new`, `fourmeme_in_hot`, `bonk_in_hot`, `nadfun_in_hot`

### Token detail

```bash
python scripts/ave_data_rest.py token --address <contract_address> --chain <chain>
```

### Token prices (batch, up to 200)

```bash
python scripts/ave_data_rest.py price --tokens <addr1>-<chain1> <addr2>-<chain2> ...
```

### Kline / candlestick data

```bash
python scripts/ave_data_rest.py kline-token --address <token> --chain <chain> [--interval <minutes>] [--size <count>]
python scripts/ave_data_rest.py kline-pair  --address <pair>  --chain <chain> [--interval <minutes>] [--size <count>]
```

Valid intervals (minutes): `1 5 15 30 60 120 240 1440 4320 10080`

### Top 100 holders

```bash
python scripts/ave_data_rest.py holders --address <token> --chain <chain>
```

### Swap transactions

```bash
python scripts/ave_data_rest.py txs --address <pair> --chain <chain>
```

### Trending tokens

```bash
python scripts/ave_data_rest.py trending --chain <chain> [--page 0] [--page-size 20]
```

### Ranked tokens by topic

```bash
python scripts/ave_data_rest.py rank-topics          # list available topics
python scripts/ave_data_rest.py ranks --topic <topic>
```

### Contract risk report

```bash
python scripts/ave_data_rest.py risk --address <token> --chain <chain>
```

### Supported chains

```bash
python scripts/ave_data_rest.py chains
```

### Main tokens on a chain

```bash
python scripts/ave_data_rest.py main-tokens --chain <chain>
```

## Formatting responses

- **Token detail**: show price, 24h change, market cap, volume, TVL, top DEX pairs, risk level
- **Kline data**: summarize trend (up/down), high/low/close; ASCII table for recent candles
- **Holders**: show top 5–10 holders with % share; flag if top 10 hold >50%
- **Swap txs**: show most recent 10 as a table (time, type, amount USD, wallet)
- **Trending/ranks**: ranked table with price, 24h change, volume
- **Risk report**: lead with risk level (LOW/MEDIUM/HIGH/CRITICAL), then key findings
- **Search**: table with symbol, name, chain, address, price, 24h change

## Reference

See `references/data-api-doc.md` for full endpoint reference.
