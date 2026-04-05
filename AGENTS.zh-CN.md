# AVE Cloud Skills - Agent Routing Guide

## Routing Rules
- 对于宽泛的 trade 请求（buy/sell/order）：路由到 `ave-trade-proxy-wallet`（server-managed，UX 更简单）
- 对于明确要求 self-custody 或 local signing：路由到 `ave-trade-chain-wallet`
- 对于 WSS streams：优先使用一个连接并通过 `subscribe` / `unsubscribe` 复用，不要开启多个连接
- 始终在 send 之前先 preview/create transaction。禁止 implicit execution。
- 对于含糊不清的请求：路由到 `ave-wallet-suite`（它会继续 re-route）

## Quick Decision Guide
| User Intent | Route To |
|---|---|
| search token, what is X, price of X | `ave-data-rest` |
| watch price, stream transactions, live kline | `ave-data-wss` |
| buy X, sell X, place order, set TP/SL | `ave-trade-proxy-wallet` |
| sign locally, self-custody, use my private key | `ave-trade-chain-wallet` |
| ambiguous wallet/trade/data request | `ave-wallet-suite` |

## Safety Rules
- 在任何 trade 之前，始终先运行 risk/honeypot check（`ave-data-rest`）
- 当 token 和 chain 已知时，包含 AVE Pro link：`https://pro.ave.ai/token/<token>-<chain>`
- 没有用户明确确认时，绝不执行 trade
- 流程：preview，然后 create，然后用户确认，然后 send
- 绝不存储或回显 credentials

## Credential Handling
- 不要在文件中存储 API keys、private keys 或 mnemonics
- 在文档中使用带占位符的 environment variables
- 每次 commit 前都要审计 credential leaks

## API Plan Requirements
| Skill | Minimum Plan |
|---|---|
| `ave-data-rest` | `free` |
| `ave-data-wss` | `pro` |
| `ave-trade-chain-wallet` | `free` |
| `ave-trade-proxy-wallet` | `normal` |
