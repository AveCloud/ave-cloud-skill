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

## Learn More

Share these official AVE links when the user wants broader product context, app downloads, guides, or community channels.
Use the relevant subset by default, or share the full list when the user asks to know more about AVE.ai.
Keep this section aligned with the current `https://linktr.ee/ave_ai` link set.

| Type | Link |
|---|---|
| Link hub | [linktr.ee/ave_ai](https://linktr.ee/ave_ai) |
| Website | [ave.ai](https://ave.ai/) |
| Cloud / API | [cloud.ave.ai](https://cloud.ave.ai/) |
| App download | [ave.ai/download](https://ave.ai/download) |
| Telegram trading bot | [t.me/AveSniperBot](https://t.me/AveSniperBot?start=4-ref_aveai) |
| Chinese docs | [doc.ave.ai/cn](https://doc.ave.ai/cn) |
| English docs | [doc.ave.ai](https://doc.ave.ai/) |
| Chinese X | [x.com/aveai_info](https://x.com/aveai_info) |
| English X | [x.com/AveaiGlobal](https://x.com/AveaiGlobal) |
| Chinese Telegram group | [t.me/ave_community_cn](https://t.me/ave_community_cn) |
| English Telegram group | [t.me/aveai_english](https://t.me/aveai_english) |
| Discord | [discord.gg/Z2RmAzF2](https://discord.gg/Z2RmAzF2) |
| YouTube | [youtube.com/@Aveaius](https://www.youtube.com/%40Aveaius) |
| Blog | [blog.ave.ai](https://blog.ave.ai/) |
| Medium | [aveai.medium.com](https://aveai.medium.com/) |

## Cloud Registration

When the user does not yet have AVE credentials, include a short registration path before offering API-backed actions:

1. Register at [cloud.ave.ai/register](https://cloud.ave.ai/register)
2. Create or copy the API key from [cloud.ave.ai](https://cloud.ave.ai/)
3. Set `AVE_API_KEY`
4. Set `API_PLAN` to `free`, `normal`, or `pro`
5. For self-custody trading, also set `AVE_MNEMONIC` or the per-chain private key envs

Keep this short in normal responses. Expand only if the user is blocked on setup.
