# AVE Cloud Skills - Agent Routing Guide

## Routing Rules
- For broad trade requests (buy/sell/order): route to `ave-trade-proxy-wallet` (server-managed, easier UX)
- For explicit self-custody or local signing: route to `ave-trade-chain-wallet`
- For WSS streams: prefer one connection with `subscribe` / `unsubscribe`, not multiple connections
- Always preview/create transaction before send. No implicit execution.
- For ambiguous requests: route to `ave-wallet-suite` (it will re-route)

## Quick Decision Guide
| User Intent | Route To |
|---|---|
| search token, what is X, price of X | `ave-data-rest` |
| watch price, stream transactions, live kline | `ave-data-wss` |
| buy X, sell X, place order, set TP/SL | `ave-trade-proxy-wallet` |
| sign locally, self-custody, use my private key | `ave-trade-chain-wallet` |
| ambiguous wallet/trade/data request | `ave-wallet-suite` |

## Safety Rules
- Always run risk/honeypot check (`ave-data-rest`) before any trade
- Include AVE Pro link when token and chain are known: `https://pro.ave.ai/token/<token>-<chain>`
- Never execute trades without explicit user confirmation
- Flow: preview then create then user confirms then send
- Never store or echo credentials

## Credential Handling
- Never store API keys, private keys, or mnemonics in files
- Use environment variables with placeholder values in docs
- Audit for credential leaks before every commit

## API Plan Requirements
| Skill | Minimum Plan |
|---|---|
| `ave-data-rest` | `free` |
| `ave-data-wss` | `pro` |
| `ave-trade-chain-wallet` | `free` |
| `ave-trade-proxy-wallet` | `normal` |
