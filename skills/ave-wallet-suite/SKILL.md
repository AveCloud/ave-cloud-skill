---
name: ave-wallet-suite
version: 2.0.0
description: |
  Route broad wallet, market-data, and trading requests across the AVE skill suite.
  Use this skill when the user asks for an AVE wallet/trading/data task but the correct sub-skill
  is not yet obvious, or when the assistant should guide the user through the full workflow.

  This skill decides between:
  - ave-data-rest for snapshot market and token data
  - ave-data-wss for live data streams
  - ave-trade-chain-wallet for self-custody trading
  - ave-trade-proxy-wallet for server-managed proxy-wallet trading
license: MIT
metadata:
  openclaw:
    primaryEnv: AVE_API_KEY
---

# ave-wallet-suite

Use this as the top-level router for AVE tasks.

## Route Selection

Choose the sub-skill by user intent:

| User intent | Use |
|---|---|
| Token search, price, holders, tx history, risk, trending | `ave-data-rest` |
| Live price / tx / kline monitoring | `ave-data-wss` |
| Self-custody trade, unsigned tx build, local signing, mnemonic/private-key flows | `ave-trade-chain-wallet` |
| Proxy wallet, order management, bot-managed execution, order status watch | `ave-trade-proxy-wallet` |

If the request mixes data and trading, do the data preflight first, then switch to the trade skill.

## First-Turn Checklist

Before acting, resolve these questions from context or by a short clarification:

1. Is this read-only data, self-custody trade, or proxy-wallet trade?
2. Is the user asking for a snapshot response or a live stream?
3. Is the user testing or placing a real order/transaction?
4. Which chain, token pair, and spend cap should be used?

For real trades, prefer the smallest practical notional and surface the spend cap explicitly.

## Default Workflow

Use this lifecycle unless the user asks for something narrower:

1. Preflight: balances, route viability, risk checks for unfamiliar tokens, minimum size constraints
2. Dry-run object: quote or create-tx / order submission preview
3. Execution: submit only once the path is valid
4. Confirmation: collect order IDs, requestTxIds, tx hashes, and status
5. Optional unwind: if this is a test trade, perform the sell-back promptly

## Response Contract

For any trade or order response, structure the answer as:

1. What happened
2. What it spent or reserved
3. Identifiers
4. What the next best action is

Always include these when present:
- `requestTxId`
- proxy order ID
- on-chain tx hash
- applied slippage / gas / fee notes

## Real-Trade Guardrails

- Default to preflight before execution
- Keep test notionals small
- Prefer immediate confirmation polling over assuming success from submission
- If a route requires approval, say so before retrying the sell path
- If a stream exists for the chosen flow, use it as a supplement, not as the only source of truth
