---
name: ave-wallet-suite
version: 2.3.0
description: |
  Route broad wallet, market-data, and trading requests across the AVE skill suite.
  Use this skill when the user asks for an AVE wallet/trading/data task but the correct sub-skill
  is not yet obvious, or when the assistant should guide the user through the full workflow.

  If the user mentions private keys, mnemonics, local signing, or self-custody, route DIRECTLY
  to ave-trade-chain-wallet — do not use this router skill.

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

Top-level router for AVE tasks. For shared operating rules, see [operator-playbook.md](../../references/operator-playbook.md).

## Route Selection

| User intent | Use |
|---|---|
| Token search, price, holders, tx history, risk, trending | `ave-data-rest` |
| Live price / tx / kline monitoring | `ave-data-wss` |
| Self-custody trade, unsigned tx build, local signing, mnemonic/private-key flows | `ave-trade-chain-wallet` |
| Proxy wallet, order management, bot-managed execution, order status watch | `ave-trade-proxy-wallet` |

If the request mixes data and trading, do the data preflight first, then switch to the trade skill.
If both proxy-wallet and chain-wallet could solve the request, prefer `ave-trade-proxy-wallet` unless the user explicitly asks for self-custody, local signing, or external signer control.

## Decision Matrix

| User says | Use | Ask first |
|---|---|---|
| "find this token", "check this CA", "is this safe" | `ave-data-rest` | chain or contract if ambiguous |
| "watch this pair", "live price", "live kline" | `ave-data-wss` | pair/token and whether they want stream or snapshots |
| "swap with my wallet", "sign locally", "use mnemonic" | `ave-trade-chain-wallet` | chain, pair, spend cap, test vs real |
| "use proxy wallet", "place bot order", "watch my order" | `ave-trade-proxy-wallet` | assetsId, chain, spend cap, test vs real |
| "I don't have an API key yet" | this skill first | whether they only need setup or also want the first action |

For broad trading requests like "buy this token" or "help me trade this", start with `ave-trade-proxy-wallet` unless the user has already chosen self-custody.

## Ambiguous Request Disambiguation

Use this table when the user request could match more than one trade skill. These are the most common misrouting patterns — resolve them here instead of asking the user.

| User says (EN) | User says (ZH) | Route to | Why |
|---|---|---|---|
| "buy this token", "swap X for Y" | "买这个币", "换成X" | `ave-trade-proxy-wallet` | Broad buy/swap defaults to proxy-wallet |
| "place a limit order", "set a buy limit" | "挂限价单", "设置限价买入" | `ave-trade-proxy-wallet` | Limit orders are proxy-wallet only |
| "set take-profit", "set stop-loss", "auto-sell" | "设置止盈", "设置止损", "自动卖出" | `ave-trade-proxy-wallet` | TP/SL/auto-sell is proxy-wallet only |
| "use my private key", "sign with my key" | "用我的私钥", "用私钥签名" | `ave-trade-chain-wallet` | Explicit private key = self-custody |
| "use my mnemonic", "use my seed phrase" | "用我的助记词", "用种子短语" | `ave-trade-chain-wallet` | Mnemonic = self-custody |
| "sign locally", "self-custody", "use my own wallet" | "本地签名", "自托管", "用我自己的钱包" | `ave-trade-chain-wallet` | Local signing = self-custody |
| "build an unsigned tx", "external signer" | "构建未签名交易", "外部签名" | `ave-trade-chain-wallet` | External signer workflow |

When the request does not match any row above, prefer `ave-trade-proxy-wallet` for trading and `ave-data-rest` for data.

## First-Turn Checklist

Before acting, resolve these from context or by short clarification:

1. Is this read-only data, self-custody trade, or proxy-wallet trade?
2. Is the user asking for a snapshot response or a live stream?
3. Is the user testing or placing a real order/transaction?
4. Which chain, token pair, and spend cap should be used?

For real trades, prefer the smallest practical notional and surface the spend cap explicitly.

## Default Workflow

1. **Preflight**: balances, route viability, risk checks for unfamiliar tokens, minimum size constraints
2. **Dry-run**: quote or create-tx / order submission preview
3. **Execution**: submit only once the path is valid
4. **Confirmation**: collect order IDs, requestTxIds, tx hashes, and status
5. **Optional unwind**: if this is a test trade, perform the sell-back promptly

## Reference

- [operator-playbook.md](../../references/operator-playbook.md) — trade path preference, WSS discipline, chat surface guidance, PROD quirks
- [error-translation.md](../../references/error-translation.md) — unified error table across all skills
- [safe-test-defaults.md](../../references/safe-test-defaults.md) — per-chain spend caps and abort rules
- [token-conventions.md](../../references/token-conventions.md) — address formatting, fee pairing, trading params, signing
- [response-contract.md](../../references/response-contract.md) — response templates, state handoff, agent modes, recovery
- [presentation-guide.md](../../references/presentation-guide.md) — token card format, kline, risk, and holder templates
- [learn-more.md](../../references/learn-more.md) — AVE links and cloud registration
