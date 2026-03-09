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

## Decision Matrix

Use this quick router when the user request is broad or ambiguous:

| User says | Use | Ask first |
|---|---|---|
| "find this token", "check this CA", "is this safe" | `ave-data-rest` | chain or contract if ambiguous |
| "watch this pair", "live price", "live kline" | `ave-data-wss` | pair/token and whether they want stream or snapshots |
| "swap with my wallet", "sign locally", "use mnemonic" | `ave-trade-chain-wallet` | chain, pair, spend cap, test vs real |
| "use proxy wallet", "place bot order", "watch my order" | `ave-trade-proxy-wallet` | assetsId, chain, spend cap, test vs real |
| "I don't have an API key yet" | this skill first | whether they only need setup or also want the first action |

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

## Safe Test Defaults

Use these unless the user explicitly asks for a different test size:

| Chain | Default test input | Cap guidance |
|---|---|---|
| BSC chain-wallet | `0.0005 BNB` | keep gas under `0.0003 BNB`; abort if route or gas spikes |
| Solana chain-wallet | `0.0005 SOL` | keep total fee budget under `0.0005 SOL`; abort if higher |
| BSC proxy-wallet | `0.0005 BNB` | verify funded wallet and sell back promptly |
| Solana proxy-wallet | start at `0.002 SOL` if smaller sizes fail | prefer smallest accepted route size |

Always surface the cap before the real test starts.

## Chain And Token Conventions

Use these conventions consistently across AVE responses and command construction:

| Topic | Convention |
|---|---|
| EVM native token placeholder | `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` |
| Solana native token input | `sol` |
| Token search identifiers | prefer `contract-chain` for batch price and live price subscriptions |
| EVM addresses in user output | preserve the chain's normal display style; lowercase only when the API requires normalization |
| Solana identifiers | use mint addresses or wallet addresses exactly as provided; do not lowercase |

Common test fixtures that are already proven in this repo:

| Chain | Token | Address / Symbol |
|---|---|---|
| BSC | USDT | `0x55d398326f99059fF775485246999027B3197955` |
| BSC | BTCB | `0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c` |
| BSC | WBNB | `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` |
| Solana | SOL | `sol` |
| Solana | USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |

## Error Translation

Translate low-level API failures into direct operator guidance:

| Raw issue pattern | Tell the user |
|---|---|
| missing API key / auth failed | credentials are missing or invalid |
| HMAC signature mismatch | the secret key does not match; regenerate at cloud.ave.ai |
| unsupported parameter / invalid parameter | the chosen parameter combination is not accepted by PROD |
| insufficient balance | the wallet does not have enough spend token or gas token |
| approval required / allowance too low | approval is needed before the sell or token spend can proceed |
| route too small / min notional failure | the trade size is below the route minimum; increase size slightly |
| RPC required | a user RPC node is required for local EVM signing |
| RPC connection refused / timeout | the RPC endpoint is unreachable; try a different RPC URL |
| transaction reverted / execution failed | the on-chain tx failed; check slippage, gas, or token tax |
| server not running | the Docker WSS daemon must be started before using server mode |
| plan not supported | this feature requires a higher API plan tier |

Prefer the translated explanation in the response, with the raw error kept as supporting detail only when useful.

## Reusable Response Templates

Use these compact shapes consistently:

- Token search: one primary token card, then compact alternates if needed
- Risk check: `risk level -> key flags -> tax/owner/honeypot notes -> next action`
- Quote: `pair -> input -> estimated output -> route notes -> next action`
- Create tx: `what was created -> input/fee/slippage -> requestTxId -> sign/send next`
- Submission: `submitted/confirmed -> spend + fees -> tx hash/order ID -> monitor or sell-back next`

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
