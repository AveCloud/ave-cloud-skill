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

## Rate Limits

| `API_PLAN` | Read TPS |
|---|---|
| `free` | 1 |
| `normal` | 5 |
| `pro` | 20 |

## Supported Chains

Covers 130+ chains. Common chain IDs: `bsc`, `eth`, `base`, `solana`, `tron`, `polygon`, `arbitrum`, `avalanche`, `sui`, `ton`, `aptos`

Use `python scripts/ave_data_rest.py chains` to list all supported chain identifiers.

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

General: `hot`, `new`, `meme`, `alpha`, `gold`, `inclusion`, `bsc_hot`

Launchpad-specific platforms follow the pattern `{launchpad}_{in|out}_{hot|new|almost}`:

| Launchpad | Chains | Prefixes |
|---|---|---|
| `pump` / `pump_all` | Solana | `pump_in_hot`, `pump_in_new`, `pump_in_almost`, `pump_out_hot`, `pump_out_new` |
| `fourmeme` | BSC | `fourmeme_in_hot`, `fourmeme_in_new`, `fourmeme_in_almost`, `fourmeme_out_hot`, `fourmeme_out_new` |
| `bonk` | Solana | `bonk_in_hot`, `bonk_in_new`, `bonk_in_almost`, `bonk_out_hot`, `bonk_out_new` |
| `nadfun` | Monad | `nadfun_in_hot`, `nadfun_in_new`, `nadfun_in_almost`, `nadfun_out_hot`, `nadfun_out_new` |
| `boop` | Solana | `boop_in_hot`, `boop_in_new`, `boop_in_almost`, `boop_out_hot`, `boop_out_new` |
| `cookpump` | — | `cookpump_in_hot`, `cookpump_in_new`, `cookpump_in_almost`, `cookpump_out_hot`, `cookpump_out_new` |
| `flap` / `xflap` | — | `flap_in_hot`, `xflap_in_hot`, etc. |
| `grafun` | — | `grafun_in_hot`, `grafun_in_new`, `grafun_in_almost`, `grafun_out_hot`, `grafun_out_new` |
| `meteora` | Solana | `meteora_in_hot`, `meteora_in_new`, `meteora_out_hot`, `meteora_out_new` |
| `sunpump` | Tron | `sunpump_in_hot`, `sunpump_in_new`, `sunpump_in_almost`, `sunpump_out_hot`, `sunpump_out_new` |
| Others | Various | `baseapp`, `basememe`, `bn`, `bankr`, `clanker`, `heaven`, `klik`, `moonshot`, `movepump`, `popme`, `xdyorswap`, `zoracontent`, `zoracreator` |

Suffix meanings: `in` = still on launchpad, `out` = graduated to DEX, `hot` = trending, `new` = recently launched, `almost` = near graduation

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

## Workflow Examples

### Token due diligence

```bash
# 1. Search by name
python scripts/ave_data_rest.py search --keyword "DOGE" --chain bsc --limit 5

# 2. Get full token detail (price, TVL, volume, pairs)
python scripts/ave_data_rest.py token --address 0xbA2aE424d960c26247Dd6c32edC70B295c744C43 --chain bsc

# 3. Check risk/honeypot report
python scripts/ave_data_rest.py risk --address 0xbA2aE424d960c26247Dd6c32edC70B295c744C43 --chain bsc

# 4. Check holder concentration
python scripts/ave_data_rest.py holders --address 0xbA2aE424d960c26247Dd6c32edC70B295c744C43 --chain bsc
```

Present as: search card → risk summary (LOW/MED/HIGH) → holder concentration warning if top 10 > 50%.

### Multi-token price comparison

```bash
# Batch query up to 200 tokens
python scripts/ave_data_rest.py price \
  --tokens 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c-bsc \
           0x2170Ed0880ac9A755fd29B2688956BD959F933F8-bsc \
           EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v-solana
```

Present as: price table with 24h change, sorted by market cap.

## Formatting responses

- **Token detail**: show price, 24h change, market cap, volume, TVL, top DEX pairs, risk level
- **Kline data**: summarize trend (up/down), high/low/close; ASCII table for recent candles
- **Holders**: show top 5–10 holders with % share; flag if top 10 hold >50%
- **Swap txs**: show most recent 10 as a table (time, type, amount USD, wallet)
- **Trending/ranks**: ranked table with price, 24h change, volume
- **Risk report**: lead with risk level (LOW/MEDIUM/HIGH/CRITICAL), then key findings
- **Search**: table with symbol, name, chain, address, price, 24h change

## Error Translation

When the API response is vague, translate it into operator terms:

| Raw issue pattern | User-facing explanation |
|---|---|
| missing API key / auth failed | credentials are missing or invalid; check `AVE_API_KEY` |
| HTTP 429 / rate limit exceeded | too many requests; wait and retry after the rate limit window resets |
| invalid token_ids | the token identifier format or filter combination is not accepted |
| token not found | AVE has no matching token record for that chain/address right now |
| empty holder list on a known token | endpoint returned no holder data; treat as data unavailability, not proof of zero holders |
| unsupported chain | the chain id is not supported by this endpoint |
| kline returns more points than requested | the API ignored `limit`; client-side trimming is applied automatically |
| empty risk report on a valid token | the risk endpoint has no data for this token; do not treat as "safe" |

## Token Search Presentation

For token search, do not dump raw JSON. Prefer an AVE Telegram-style token card for chat surfaces.

Use this layout when enough fields are available:

```text
📌 【chain】 SYMBOL (ProjectName)
📄 合约: 0x...

⚖️ Dex: ...
💲 价格: $...
💰 市值: $...
💧 流动性: $...
🪙 交易对: ...
📈 15m: ..., 24h: ...
🎯 狙击人: ...  抢购人: ...
🕠 开盘时间: ...

👥 持有人: ...(top holder summary)
👨‍🍳创建者 ... 钱包地址
🔍 检测: 分数: ...(风险等级)
买入税: ...  卖出税: ...
⚠️...

🔥 首次喊单 ... ... (...分)
```

Presentation rules:
- Prefer the exact field order above for Chinese / Telegram-style responses
- Omit lines that are not available instead of inventing data
- Keep labels in Chinese when the user is operating in Chinese or the output is clearly intended for Telegram community style
- If the user is operating in English, keep the same card structure but translate labels
- Shorten long addresses only when space is constrained; otherwise show the full contract on the main contract line
- Use `0.0{n}1234` style formatting for very small prices when that improves readability
- If multiple chains or duplicate symbols exist, say that first, then show the top 3 to 5 candidate cards
- If there is one obvious best match, show one full card and list the other candidates more compactly below it

Desktop / API-style fallback:
- Use a concise Markdown table first
- Then show one highlighted card in the same field order when a primary result is clear

## Learn More

- API docs: [cloud.ave.ai](https://cloud.ave.ai/)
- Register: [cloud.ave.ai/register](https://cloud.ave.ai/register)
- Community: [t.me/aveai_english](https://t.me/aveai_english) | [discord.gg/Z2RmAzF2](https://discord.gg/Z2RmAzF2)

## Reference

See `references/data-api-doc.md` for full endpoint reference.
