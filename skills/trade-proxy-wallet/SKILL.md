---
name: ave-trade-proxy-wallet
version: 2.0.0
description: |
  Execute server-managed (proxy wallet) DEX trades via the AVE Cloud Bot Trade API (https://bot-api.ave.ai).
  Use this skill whenever the user wants to:
  - Place a market (immediate) swap order via a proxy wallet
  - Place a limit order that triggers when a token hits a target price
  - Set take-profit or stop-loss rules on a market order (auto-sell)
  - Set a trailing take-profit rule on a market order
  - List, create, or delete proxy (bot) wallets
  - Cancel pending limit orders
  - Approve a token for trading on EVM chains (proxy wallet)
  - Check token approval status
  - Transfer tokens from a delegate proxy wallet
  - Query market order or limit order history
  - Watch real-time order status updates via WebSocket push

  Requires API_PLAN=normal or pro. Proxy wallets are server-managed by Ave — no local signing required.

  DO NOT use this skill for:
  - Self-custody trading where the user holds private keys → use ave-trade-chain-wallet instead
  - On-chain data queries → use ave-data-rest instead
  - Real-time price/tx/kline streams → use ave-data-wss instead
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

Server-managed (proxy wallet) DEX trading via the AVE Cloud Bot Trade API.
Requires `API_PLAN=normal` or `pro`. No local signing — Ave manages wallet keys server-side.

**Trading fee:** 0.8% | **Rebate to `feeRecipient`:** 25%

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

## Wallet Management

```bash
# List proxy wallets (optionally filter by assetsIds)
python scripts/ave_trade_rest.py list-wallets [--assets-ids id1,id2]

# Create a new delegate proxy wallet
python scripts/ave_trade_rest.py create-wallet --name "my-wallet" [--return-mnemonic]

# Delete delegate proxy wallets
python scripts/ave_trade_rest.py delete-wallet --assets-ids id1 id2
```

## Market Trading

Places an immediate swap order. Proxy wallet executes server-side.

```bash
python scripts/ave_trade_rest.py market-order \
  --chain solana \
  --assets-id 1cbac4a6674a419f88208b9f7b90cd45 \
  --in-token sol \
  --out-token 3gWxcrL1KiZp9P6zVgNsiNnF8N3zYw2Vic4usW4ipump \
  --in-amount 1000000 \
  --swap-type buy \
  --slippage 500 \
  --use-mev \
  [--auto-slippage] \
  [--auto-gas average] \
  [--gas 50000000] \
  [--extra-gas 1000000000] \
  [--auto-sell '{"priceChange":"-5000","sellRatio":"10000","type":"default"}'] ...
```

`--auto-sell` is repeatable: max 10 `default` rules + 1 `trailing` rule per order.

**Auto-sell rule fields:**
- `priceChange`: bps threshold (e.g. `"5000"` = +50%, `"-9000"` = -90%; trailing: drawdown ratio)
- `sellRatio`: bps of tokens to sell (e.g. `"10000"` = 100%)
- `type`: `default` (price target) or `trailing` (peak then drop)

## Limit Trading

Places a limit order that executes when the token reaches `limitPrice` (USD).

```bash
python scripts/ave_trade_rest.py limit-order \
  --chain solana \
  --assets-id 1cbac4a6674a419f88208b9f7b90cd45 \
  --in-token sol \
  --out-token 3gWxcrL1KiZp9P6zVgNsiNnF8N3zYw2Vic4usW4ipump \
  --in-amount 1000000 \
  --swap-type buy \
  --slippage 500 \
  --use-mev \
  --limit-price 15.5 \
  [--expire-time 86400] \
  [--auto-slippage] \
  [--auto-gas average]
```

## Query Orders

```bash
# Market orders by IDs
python scripts/ave_trade_rest.py get-swap-orders --chain solana --ids id1,id2

# Limit orders (paginated)
python scripts/ave_trade_rest.py get-limit-orders \
  --chain solana \
  --assets-id 1cbac4a6... \
  --page-size 20 \
  --page-no 0 \
  [--status waiting] \
  [--token <token_address>]
```

## Cancel Limit Order

```bash
python scripts/ave_trade_rest.py cancel-limit-order --chain solana --ids id1 id2
```

## Token Approval (EVM only)

Before trading EVM tokens, approve the token for the router contract. Not needed for native coins.

```bash
# Approve
python scripts/ave_trade_rest.py approve-token \
  --chain bsc \
  --assets-id 1cbac4a6... \
  --token-address 0xa5e4ccf...

# Check approval status
python scripts/ave_trade_rest.py get-approval --chain bsc --ids approval_id1,approval_id2
```

## Transfer (delegate wallets only)

```bash
python scripts/ave_trade_rest.py transfer \
  --chain bsc \
  --assets-id 1cbac4a6... \
  --from-address 0xa5e4... \
  --to-address 0x2be4... \
  --token-address 0x55d3... \
  --amount 1000000000000000000 \
  [--extra-gas 1000000000]

# Check transfer status
python scripts/ave_trade_rest.py get-transfer --chain bsc --ids transfer_id1
```

## Watch Order Status (WebSocket)

Subscribes to real-time proxy wallet order push notifications.

```bash
python scripts/ave_trade_wss.py watch-orders
```

Connects to `wss://bot-api.ave.ai/thirdws?ave_access_key={AVE_API_KEY}`, subscribes to topic `botswap`.
Each push message includes: `id`, `status`, `chain`, `assetsId`, `orderType`, `swapType`, `txHash`, `errorMessage`.

Press Ctrl+C to stop.

## Reference

See `references/trade-api-doc.md` → Proxy Wallet Trading and WebSocket Push sections.
