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
For shared connection discipline and cross-skill operating rules, see [operator-playbook.md](../../references/operator-playbook.md).

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

## Rate Limits

WebSocket streams require `API_PLAN=pro` (20 TPS).

Connection discipline matters more than TPS:
- Prefer one live connection with `subscribe` / `unsubscribe` over opening multiple parallel sockets
- Treat 5 concurrent connections as the practical ceiling for a single operator session
- If the user wants to watch multiple topics, reuse the same REPL or server connection when possible
- Close or unsubscribe from old streams before opening more

## Supported Chains

All chains available in the Data REST API are supported for WebSocket streams. Common: `bsc`, `eth`, `base`, `solana`, `tron`, `polygon`, `arbitrum`

## Operations

## Chat Surface Rules

For OpenClaw, Claude, and Codex chat surfaces:

- prefer one active connection with multiple `subscribe` / `unsubscribe` operations
- prefer short periodic summaries over forwarding every raw event
- avoid wide raw JSON dumps unless the user explicitly asks for debugging detail
- use Markdown-friendly cards or ASCII snapshots for kline updates
- if the user is on a mobile/chat surface, keep each live update compact enough to scan in one screen

### Interactive REPL (recommended for live monitoring)

```bash
# Preferred: local CLI with Docker-managed runtime
python scripts/ave_data_wss.py wss-repl

# Fallback: direct Docker invocation only when debugging runtime issues
docker run -it -e AVE_API_KEY -e API_PLAN=pro ave-cloud wss-repl
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
Prefer this REPL or the Docker server daemon for multi-topic monitoring, because it reuses one connection.

For agent-driven sessions, prefer:
1. open one REPL/server connection
2. `subscribe` to the current topic
3. `unsubscribe` before switching topics
4. keep total concurrent connections under 5

### Stream live swap/liquidity events

```bash
python scripts/ave_data_wss.py watch-tx --address <pair_address> --chain <chain> [--topic tx]
```

`--topic` choices: `tx` (default), `multi_tx`, `liq`

### Stream live kline updates

```bash
python scripts/ave_data_wss.py watch-kline --address <pair_address> --chain <chain> [--interval k60] [--format raw|markdown]
```

`--interval` choices: `s1 k1 k5 k15 k30 k60 k120 k240 k1440 k10080`
`--format markdown` enables the ASCII mini-chart formatter.
Formatted mode can run directly in Docker even if the background daemon is not already running.

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

Use the daemon when the assistant needs to maintain one reusable connection and swap subscriptions over time.

## Workflow Examples

### Monitor a new token launch

```bash
# 1. Start REPL
python scripts/ave_data_wss.py wss-repl

# 2. Subscribe to swap events on the token's pair
> subscribe tx <pair_address> bsc

# 3. Watch for buy/sell volume pattern (stream runs until unsubscribe)
# Agent should summarize: buy vs sell count, large txs, price direction

# 4. Switch to price monitoring
> unsubscribe
> subscribe price <token_address>-bsc

# 5. Exit
> quit
```

### Kline monitoring with Docker daemon

```bash
# 1. Start persistent server
python scripts/ave_data_wss.py start-server

# 2. Reuse the same connection for one topic at a time
python scripts/ave_data_wss.py watch-kline --address <pair_address> --chain bsc --interval k1 --format markdown

# 3. When you need a different topic, unsubscribe or switch in the REPL/server flow
#    instead of opening another fresh connection

# 4. When done, stop the server
python scripts/ave_data_wss.py stop-server
```

### Agent-run monitoring sequence

Use this sequence for OpenClaw, Claude, or Codex when the assistant is actively driving the monitoring flow:

```text
1. Start one reusable connection (REPL or server daemon)
2. Subscribe to the current topic
3. Summarize periodically instead of forwarding every event
4. Unsubscribe before switching topics
5. Stop the server or exit the REPL when monitoring is complete
```

## Live Kline Presentation

For OpenClaw users, do not treat raw JSON as the primary experience for live kline monitoring.

Preferred presentation order:

1. Best UX when possible: render a chart artifact or rich visual view
2. Chat-friendly fallback: periodic Markdown snapshots with an ASCII mini-chart
3. Raw JSON stream only when the user explicitly asks for raw events or piping

For the Markdown fallback, prefer a compact format like:

```text
[bsc] TOKEN / QUOTE 1m
O: 0.0000766  H: 0.0000781  L: 0.0000759  C: 0.0000774
15m: -12.14%   24h: +130.85%
Vol: $21.1K

0.0000790 |   ╭╮
0.0000780 |  ╭╯╰╮
0.0000770 | ╭╯  ╰╮
0.0000760 |╭╯    ╰
0.0000750 |╯
```

Guidelines:
- Refresh on a reasonable cadence instead of flooding the chat
- Summarize the latest candle and short-term direction above the chart
- Keep the ASCII chart narrow enough to render cleanly in Markdown
- If a richer chart or image is available in the client, prefer that over ASCII
- Prefer resolved token symbols in the header when pair metadata is available; otherwise abbreviate the pair address cleanly
- Prefer reusing the same live connection and changing subscriptions rather than opening a fresh socket for each watch

Recommended cadence:
- active trading: summarize every 5 to 15 seconds
- passive monitoring: summarize every 30 to 60 seconds
- always suppress duplicate no-change updates unless the user asked for every tick

Compact live update template:

```text
[bsc] TOKEN/USDT 1m
O: 0.0000766  H: 0.0000781  L: 0.0000759  C: 0.0000774
Move: +1.05%   Vol: $21.1K
Trend: steady climb
```

## Error Translation

| Raw issue pattern | User-facing explanation |
|---|---|
| connection closed / EOF | WebSocket disconnected; reconnect or restart the REPL |
| invalid API key / auth failed | credentials are missing or invalid; check `AVE_API_KEY` |
| plan not supported | WebSocket streams require `API_PLAN=pro` |
| subscribe failed / unknown topic | the subscription topic or address format is not accepted |
| server not running | the Docker WSS daemon must be started with `start-server` first |
| pipe not found / FIFO error | the named pipe `/tmp/ave_pipe` is missing; restart the server container |

## Learn More

- API docs: [cloud.ave.ai](https://cloud.ave.ai/)
- Register: [cloud.ave.ai/register](https://cloud.ave.ai/register)
- Community: [t.me/aveai_english](https://t.me/aveai_english) | [discord.gg/Z2RmAzF2](https://discord.gg/Z2RmAzF2)

## Reference

See `references/data-api-doc.md` for full WebSocket API reference.
