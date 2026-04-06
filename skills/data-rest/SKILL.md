---
name: ave-data-rest
version: 2.2.0
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

Snapshot on-chain token data via the AVE Cloud Data REST API. For shared operating rules and response norms, see [operator-playbook.md](../../references/operator-playbook.md).

## Setup
```bash
export AVE_API_KEY="your_api_key_here"
export API_PLAN="free"   # free | normal | pro
```
Get a free key at https://cloud.ave.ai/register.

## Rate Limits
| `API_PLAN` | Read TPS |
|---|---|
| `free` | 1 |
| `normal` | 5 |
| `pro` | 20 |

## Supported Chains
130+ chains, including `bsc`, `eth`, `base`, `solana`, `tron`, `polygon`, `arbitrum`, `avalanche`, `sui`, `ton`, `aptos`.

## Operations

### Search tokens
Find tokens by keyword, symbol, or contract.
```bash
python scripts/ave_data_rest.py search --keyword <keyword> [--chain <chain>] [--limit 20]
```

### Platform tokens
Browse launchpad or topic feeds by platform tag.
```bash
python scripts/ave_data_rest.py platform-tokens --platform <platform>
```
Examples: `hot`, `new`, `meme`, `pump_in_hot`, `pump_out_new`, `fourmeme_in_hot`, `bonk_out_hot`, `nadfun_in_new`. Suffixes: `in` = on launchpad, `out` = on DEX, `hot` = trending, `new` = recent, `almost` = near graduation.

### Token detail
Get price, liquidity, volume, pairs, and token summary.
```bash
python scripts/ave_data_rest.py token --address <contract_address> --chain <chain>
```
AVE Pro deep link: `https://pro.ave.ai/token/<contract_address>-<chain>`

### Token prices
Batch price lookup for up to 200 `address-chain` identifiers.
```bash
python scripts/ave_data_rest.py price --tokens <addr1>-<chain1> <addr2>-<chain2> ...
```

### Token kline
Get OHLCV candles by token address.
```bash
python scripts/ave_data_rest.py kline-token --address <token> --chain <chain> [--interval <minutes>] [--size <count>]
```

### Pair kline
Get OHLCV candles by pair address.
```bash
python scripts/ave_data_rest.py kline-pair --address <pair> --chain <chain> [--interval <minutes>] [--size <count>]
```

### Holders
Get the top 100 holders for a token.
```bash
python scripts/ave_data_rest.py holders --address <token> --chain <chain>
```

### Transactions
Get recent swap transactions for a pair.
```bash
python scripts/ave_data_rest.py txs --address <pair> --chain <chain>
```

### Trending
Get trending tokens for a chain.
```bash
python scripts/ave_data_rest.py trending --chain <chain> [--page 0] [--page-size 20]
```

### Rank topics
List available ranking topics.
```bash
python scripts/ave_data_rest.py rank-topics
```

### Ranks
Get ranked tokens for a topic.
```bash
python scripts/ave_data_rest.py ranks --topic <topic>
```

### Risk
Run the contract security and honeypot report.
```bash
python scripts/ave_data_rest.py risk --address <token> --chain <chain>
```

### Chains
List supported chain identifiers.
```bash
python scripts/ave_data_rest.py chains
```

### Main tokens
Get the main or native tokens for a chain.
```bash
python scripts/ave_data_rest.py main-tokens --chain <chain>
```

## Workflow Example
Run search -> token -> risk -> holders before discussing a new token.
```bash
python scripts/ave_data_rest.py search --keyword "DOGE" --chain bsc --limit 5
python scripts/ave_data_rest.py token --address 0xbA2aE424d960c26247Dd6c32edC70B295c744C43 --chain bsc
python scripts/ave_data_rest.py risk --address 0xbA2aE424d960c26247Dd6c32edC70B295c744C43 --chain bsc
python scripts/ave_data_rest.py holders --address 0xbA2aE424d960c26247Dd6c32edC70B295c744C43 --chain bsc
```

## Reference
Use shared references for operator rules, response shape, presentation, and fuller API details when the task needs more than the CLI surface here.
- [operator-playbook.md](../../references/operator-playbook.md)
- [error-translation.md](../../references/error-translation.md)
- [response-contract.md](../../references/response-contract.md)
- [presentation-guide.md](../../references/presentation-guide.md)
- [learn-more.md](../../references/learn-more.md)
- [data-api-doc.md](../../references/data-api-doc.md)
