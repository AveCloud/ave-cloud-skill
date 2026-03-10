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
This should be the default AVE trading path when the user does not explicitly require self-custody.
For shared trade-path preference and current PROD quirks, see [operator-playbook.md](../../references/operator-playbook.md).

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

## Token And Address Conventions

- EVM native token orders use `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee`
- Solana native token orders use `sol`
- EVM token approvals are only for ERC-20 style tokens, not native coins
- Preserve Solana addresses exactly as provided
- If `feeRecipient` is set, pair it with `feeRecipientRate`

## First-Turn Playbook

For a new proxy-wallet trading request:

1. Verify whether the user already has an `assetsId`; if not, create a disposable wallet first
2. Check that the proxy wallet is funded on the target chain before placing a real order
3. Use the smallest practical real order size, and respect chain-specific minimums
4. Open `watch-orders` when live status feedback is useful, but still confirm by querying order IDs directly

If the request could be handled by either proxy-wallet or chain-wallet, stay on proxy-wallet unless the user explicitly asks for local signing, mnemonic use, hardware wallet flow, or external signer control.

## State To Preserve

Once known, keep these visible across turns:

- `assetsId`
- chain
- input token
- output token
- input amount
- proxy order ID
- tx hash
- whether `watch-orders` is already running

Next-turn restatement template:

```text
State:
- chain: ...
- assetsId: ...
- pair: ... -> ...
- order ID: ...
- tx hash: ...
- watch-orders: running / not running
```

## Safe Test Defaults

Use these defaults for first real tests unless the user provides stricter limits:

- BSC proxy buy test: `0.0005 BNB`
- Solana proxy buy test: start at `0.002 SOL` if smaller sizes are rejected by the route
- Use a disposable wallet for testing when possible
- After a test buy confirms, prefer an immediate sell-back instead of leaving exposure open

If the wallet is unfunded, stop and ask for funding before submitting the order.

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

If `AVE_USE_DOCKER=true`, the CLI re-execs into Docker like the other AVE scripts. No separate manual Docker invocation is required.

Connects to `wss://bot-api.ave.ai/thirdws?ave_access_key={AVE_API_KEY}`, subscribes to topic `botswap`.
Each push message includes: `id`, `status`, `chain`, `assetsId`, `orderType`, `swapType`, `txHash`, `errorMessage`.

Press Ctrl+C to stop.

Offer `watch-orders` automatically after a real proxy order submission unless the user asked for a quiet, terse response.

Use this rule consistently:
- WebSocket is for live visibility and fast updates
- REST order queries are the source of truth for final status, retries, and post-trade reporting

For chat-first clients, summarize order pushes instead of dumping every raw event:
- `submitted`
- `confirmed`
- `error`
- `cancelled`

Example order update:

```text
Order confirmed: solana buy
assetsId: ...
Order ID: ...
Tx hash: ...
Next: sell back if this was a test
```

## Workflow Examples

### Full proxy wallet lifecycle (create → buy → monitor → sell → cleanup)

```bash
# 1. Create a disposable test wallet
python scripts/ave_trade_rest.py create-wallet --name "test-bot-1"
# → Note assetsId and wallet addresses per chain

# 2. User funds the wallet (transfer SOL to the Solana address)

# 3. Place a market buy with stop-loss protection
python scripts/ave_trade_rest.py market-order --chain solana \
  --assets-id <assetsId> \
  --in-token sol \
  --out-token 3gWxcrL1KiZp9P6zVgNsiNnF8N3zYw2Vic4usW4ipump \
  --in-amount 2000000 --swap-type buy --slippage 500 --use-mev \
  --auto-sell '{"priceChange":"-5000","sellRatio":"10000","type":"default"}'
# → Returns order ID

# 4. Monitor order status via WebSocket
python scripts/ave_trade_wss.py watch-orders
# → Wait for "confirmed" status with txHash

# 5. Check order result
python scripts/ave_trade_rest.py get-swap-orders --chain solana --ids <order_id>

# 6. Sell back
python scripts/ave_trade_rest.py market-order --chain solana \
  --assets-id <assetsId> \
  --in-token 3gWxcrL1KiZp9P6zVgNsiNnF8N3zYw2Vic4usW4ipump \
  --out-token sol --in-amount <full_token_balance> \
  --swap-type sell --slippage 500 --use-mev

# 7. Cleanup: delete the test wallet
python scripts/ave_trade_rest.py delete-wallet --assets-ids <assetsId>
```

### EVM limit order with approval

```bash
# 1. Approve the ERC-20 token for trading (one-time per token)
python scripts/ave_trade_rest.py approve-token --chain bsc \
  --assets-id <assetsId> --token-address 0x55d3...

# 2. Check approval status
python scripts/ave_trade_rest.py get-approval --chain bsc --ids <approval_id>
# → Wait for confirmed status

# 3. Place a limit sell order
python scripts/ave_trade_rest.py limit-order --chain bsc \
  --assets-id <assetsId> \
  --in-token 0x55d3... --out-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee \
  --in-amount 1000000000000000000 --swap-type sell \
  --slippage 500 --use-mev --limit-price 1.05 --expire-time 86400

# 4. Check or cancel
python scripts/ave_trade_rest.py get-limit-orders --chain bsc --assets-id <assetsId> --status waiting
python scripts/ave_trade_rest.py cancel-limit-order --chain bsc --ids <order_id>
```

## Trading Parameter Reference

| Parameter | Type | Description |
|---|---|---|
| `--slippage` | integer (bps) | Max slippage tolerance. `500` = 5%, `1000` = 10% |
| `--auto-slippage` | flag | Let the API auto-adjust slippage based on token volatility |
| `--use-mev` | flag | Enable MEV protection (front-running bundling) |
| `--gas` | string | Manual gas/priority fee in smallest unit (wei for EVM, lamports for Solana) |
| `--extra-gas` | string | Additional gas on top of estimated amount |
| `--auto-gas` | `low` / `average` / `high` | Auto gas estimation tier. Recommended: `average` |
| `--fee-recipient` | address | Wallet to receive fee rebate. Must pair with `--fee-recipient-rate` |
| `--fee-recipient-rate` | integer (bps) | Rebate ratio, max 1000 (10%). Must pair with `--fee-recipient` |
| `--limit-price` | float (USD) | Target price for limit orders |
| `--expire-time` | integer (seconds) | Limit order expiry. `86400` = 24 hours |

**Units:**
- EVM amounts: wei (1 BNB = 10^18 wei)
- Solana amounts: lamports (1 SOL = 10^9 lamports)
- Slippage/rates: basis points (1 bps = 0.01%)

## Response Contract

After every proxy-wallet action, answer in this order:

1. Outcome: wallet created, order submitted, order confirmed, order failed, or order cancelled
2. Funding or spend context: which wallet, which chain, and how much was used
3. Identifiers: `assetsId`, order ID, and tx hash if confirmed
4. Next step: poll order, watch `botswap`, place the sell-back, or clean up the wallet

Treat WebSocket events as confirmation aids, not as the only evidence of final status.

## Error Translation

Map common proxy-wallet failures into direct operator guidance:

| Raw issue pattern | User-facing explanation |
|---|---|
| missing API key / auth failed | credentials are missing or invalid; check `AVE_API_KEY` and `AVE_SECRET_KEY` |
| HMAC signature mismatch | the secret key does not match; regenerate `AVE_SECRET_KEY` at cloud.ave.ai |
| user account not exist or deactivated | the proxy wallet account is missing or inactive |
| transaction not found / approve not found | the requested order or approval id does not exist |
| invalid parameter | the chosen order parameters are not accepted by PROD |
| insufficient balance | the proxy wallet needs more spend token or native gas token |
| route too small / min notional failure | the order size is below the route minimum; increase size slightly |
| approval required (EVM sell) | approve the ERC-20 token for the router before selling |
| success with empty cancel response | the cancel request was accepted, but there may be no active order data to return |
| order status `error` in WebSocket push | check `errorMessage` in the push event for the root cause |

Prefer the translated explanation first, and keep the raw API message only as supporting detail.

## Response Templates

- Wallet create:
  `Proxy wallet created: <assetsId> on <supported chains>. Next: fund the wallet or place a test order.`
- Market order:
  `Order submitted: <chain> <buy/sell> via proxy wallet <assetsId>. Spend: <amount/token>. IDs: <order id>. Next: watch orders or poll status.`
- Limit order:
  `Limit order placed: trigger price <value>. IDs: <order id>. Next: monitor or cancel if conditions change.`
- Order confirmation:
  `Order confirmed: <order id>, tx hash <hash>. Spend/result: <summary>. Next: sell back, monitor, or clean up the wallet.`

## Learn More

- API docs: [cloud.ave.ai](https://cloud.ave.ai/)
- Register: [cloud.ave.ai/register](https://cloud.ave.ai/register)
- Community: [t.me/aveai_english](https://t.me/aveai_english) | [discord.gg/Z2RmAzF2](https://discord.gg/Z2RmAzF2)

## Reference

See `references/trade-api-doc.md` → Proxy Wallet Trading and WebSocket Push sections.
