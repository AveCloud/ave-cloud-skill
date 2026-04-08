---
name: ave-trade-proxy-wallet
version: 2.3.0
description: |
  Execute server-managed proxy-wallet DEX trades via the AVE Cloud Bot Trade API.
  Use this skill for proxy-wallet market and limit orders, TP/SL or trailing exits,
  proxy wallet lifecycle actions, EVM token approvals, delegate transfers, order-history
  queries, and live order-status watching over WebSocket.

  Requires API_PLAN=normal or pro. Proxy wallets are managed by Ave; no local signing.

  Do not use this skill for self-custody trading, on-chain data queries, or price/tx/kline streams.
license: MIT
metadata:
  openclaw:
    primaryEnv: AVE_API_KEY
    requires:
      env:
        - AVE_API_KEY
        - AVE_SECRET_KEY
        - API_PLAN
      bins:
        - python3
---

# ave-trade-proxy-wallet

Server-managed proxy-wallet DEX trading via the AVE Cloud Bot Trade API. This is the default AVE trading path when the user has not explicitly asked for self-custody. For shared trade-path rules and current PROD quirks, see [operator-playbook.md](../../references/operator-playbook.md).

**Trading fee:** 0.8% | **Rebate to `feeRecipient`:** 25%

## Route Cues

| EN | ZH |
|---|---|
| "buy this token", "swap X for Y" | "买这个币", "换成X" |
| "place a limit order", "set a buy limit" | "挂限价单", "设置限价买入" |
| "set take-profit", "set stop-loss" | "设置止盈", "设置止损" |
| "auto-sell", "trailing stop" | "自动卖出", "追踪止损" |
| "use proxy wallet", "place bot order" | "用代理钱包", "下机器人订单" |
| "watch my order", "check order status" | "看我的订单", "查询订单状态" |

## Setup

```bash
export AVE_API_KEY="your_api_key_here"
export AVE_SECRET_KEY="your_secret_key_here"
export API_PLAN="normal"   # normal | pro
pip install -r scripts/requirements.txt
```

Get keys at https://cloud.ave.ai/register. Proxy Wallet API must be activated on your account.

## Rate Limits

| `API_PLAN` | Write TPS |
|---|---|
| `normal` | 5 |
| `pro` | 20 |

## Supported Chains

`bsc`, `eth`, `base`, `solana`

Preview or query order state first when useful, and do not treat the initial submission acknowledgement as final execution status.

## Operations

### Wallet management

List, create, or delete delegate proxy wallets.

```bash
python scripts/ave_trade_rest.py list-wallets [--assets-ids id1,id2]
python scripts/ave_trade_rest.py create-wallet --name "my-wallet" [--return-mnemonic]
python scripts/ave_trade_rest.py delete-wallet --assets-ids id1 id2
```

### Market order

Place an immediate proxy-wallet swap order.

```bash
python scripts/ave_trade_rest.py market-order --chain <chain> --assets-id <assetsId> --in-token <token> --out-token <token> --in-amount <amount> --swap-type buy|sell --slippage 500 [--auto-slippage] [--use-mev] [--auto-sell '{"priceChange":"-5000","sellRatio":"10000","type":"default"}']
```

`--auto-sell` supports default TP/SL rules plus one trailing rule.

### Limit order

Place a limit order that waits for the target USD price.

```bash
python scripts/ave_trade_rest.py limit-order --chain <chain> --assets-id <assetsId> --in-token <token> --out-token <token> --in-amount <amount> --swap-type buy|sell --slippage 500 --limit-price <usd> [--expire-time 86400]
```

### Query orders

Get market or limit order status by ID or filter.

```bash
python scripts/ave_trade_rest.py get-swap-orders --chain <chain> --ids id1,id2
python scripts/ave_trade_rest.py get-limit-orders --chain <chain> --assets-id <assetsId> [--status waiting] [--token <token>] [--page-size 20] [--page-no 0]
```

### Cancel limit order

Cancel waiting limit orders.

```bash
python scripts/ave_trade_rest.py cancel-limit-order --chain <chain> --ids id1 id2
```

### Approval

Approve ERC-20 token spending for EVM proxy-wallet trading.

```bash
python scripts/ave_trade_rest.py approve-token --chain bsc --assets-id <assetsId> --token-address <token>
python scripts/ave_trade_rest.py get-approval --chain bsc --ids approval_id1,approval_id2
```

### Transfer

Move assets from a delegate proxy wallet.

```bash
python scripts/ave_trade_rest.py transfer --chain <chain> --assets-id <assetsId> --from-address <from> --to-address <to> --token-address <token> --amount <amount>
python scripts/ave_trade_rest.py get-transfer --chain <chain> --ids transfer_id1
```

### Watch orders

Stream live proxy-wallet order updates; use REST order queries as the source of truth for final status.

```bash
python scripts/ave_trade_wss.py watch-orders
```

## Workflow Example

### Disposable wallet buy flow

Create a wallet, place the order, watch it live, then confirm by order ID.

```bash
python scripts/ave_trade_rest.py create-wallet --name "test-wallet"
python scripts/ave_trade_rest.py market-order --chain solana --assets-id <assetsId> --in-token sol --out-token <token> --in-amount 2000000 --swap-type buy --slippage 500 --use-mev
python scripts/ave_trade_wss.py watch-orders
python scripts/ave_trade_rest.py get-swap-orders --chain solana --ids <order_id>
```

## Reference

Use shared references for current PROD quirks, test caps, token conventions, error wording, response shape, and fuller trade API details.

- [operator-playbook.md](../../references/operator-playbook.md)
- [error-translation.md](../../references/error-translation.md)
- [safe-test-defaults.md](../../references/safe-test-defaults.md)
- [token-conventions.md](../../references/token-conventions.md)
- [response-contract.md](../../references/response-contract.md)
- [learn-more.md](../../references/learn-more.md)
- [trade-api-doc.md](../../references/trade-api-doc.md)
