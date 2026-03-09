---
name: ave-trade-chain-wallet
version: 2.0.0
description: |
  Execute self-custody DEX trades via the AVE Cloud Chain Wallet Trading API (https://bot-api.ave.ai).
  Use this skill whenever the user wants to:
  - Get a swap quote (estimated output amount) for a token pair
  - Build an unsigned EVM transaction for a swap (BSC, ETH, Base)
  - Build an unsigned Solana transaction for a swap
  - Sign and send an EVM swap transaction using a local private key or mnemonic
  - Sign and send a Solana swap transaction using a local private key or mnemonic
  - Submit a pre-signed EVM or Solana transaction (external signer workflow)
  - Execute a self-custody DEX trade where the user controls their own private keys
  - Perform a one-step swap (create + sign + send) on EVM or Solana chains

  Available on all plan tiers (free, normal, pro). User private keys never leave the local machine.

  DO NOT use this skill for:
  - Server-managed (proxy) wallet trading → use ave-trade-proxy-wallet instead
  - On-chain data queries → use ave-data-rest instead
  - Real-time streams → use ave-data-wss instead
license: MIT
metadata:
  openclaw:
    primaryEnv: AVE_API_KEY
    requires:
      env:
        - AVE_API_KEY
      bins:
        - python3
---

# ave-trade-chain-wallet

Self-custody DEX trading via the AVE Cloud Chain Wallet API. User controls all private keys.
Available on all plan tiers (free, normal, pro).

**Trading fee:** 0.6% | **Rebate to `feeRecipient`:** 20%

Observed PROD caveats on 2026-03-09:
- EVM `--fee-recipient` should be paired with `--fee-recipient-rate`; unpaired `feeRecipient` produced misleading `feeRecipientRate` errors in PROD probes.
- Solana `--fee-recipient` should be paired with `--fee-recipient-rate`; unpaired `feeRecipient` returned a `feeRecipientRate` error in PROD.
- Create responses may apply a different `slippage` value than the requested one; report the applied value instead of assuming an echo.

## Setup

```bash
export AVE_API_KEY="your_api_key_here"
export API_PLAN="free"   # free | normal | pro

# For automatic signing (optional — required for swap-evm / swap-solana):
export AVE_EVM_PRIVATE_KEY="0x..."         # hex private key for BSC/ETH/Base
export AVE_SOLANA_PRIVATE_KEY="base58..."  # base58 private key for Solana
# OR use a BIP39 mnemonic for all chains (individual key takes priority):
export AVE_MNEMONIC="word1 word2 ... word12"

pip install -r scripts/requirements.txt
```

Get an API key at https://cloud.ave.ai/register.

## Rate Limits

| `API_PLAN` | Write TPS |
|---|---|
| `free` | 1 |
| `normal` | 5 |
| `pro` | 20 |

## Supported Chains

EVM: `bsc`, `eth`, `base`
Solana: `solana`

## Token And Address Conventions

- EVM native token input uses `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee`
- Solana native token input uses `sol`
- Pair `feeRecipient` with `feeRecipientRate` on both EVM and Solana if you set either
- Do not lowercase Solana addresses
- For EVM, preserve the user-provided address in output, but normalize only when an endpoint explicitly requires it
- Treat wrapped/native distinctions carefully in explanations: `WBNB` is a token, `BNB` is the native coin

## First-Turn Playbook

For a new chain-wallet trading request:

1. Identify whether the user wants a quote, unsigned transaction, signed send, or a full buy/sell test cycle
2. For real trades, confirm the spend cap and prefer a create-only preflight first
3. For unfamiliar tokens, pair the trade flow with a risk or liquidity sanity check before execution
4. For EVM `swap-evm`, require a user RPC node via `--rpc-url` or `AVE_<CHAIN>_RPC_URL`

Prefer the low-level `create-*` and `send-*` flow when you need tighter control over gas, fees, or request IDs.

## Safe Test Defaults

Use these defaults for first real tests unless the user gives stricter limits:

- BSC buy test: `0.0005 BNB`
- BSC gas cap: `0.0003 BNB`
- Solana buy test: `0.0005 SOL`
- Solana total priority-fee cap: `0.0005 SOL`

Abort or fall back to create-only preview if the route exceeds those caps.

## Operations

### Get swap quote

```bash
python scripts/ave_trade_rest.py quote \
  --chain bsc \
  --in-amount 10000000 \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x2170Ed0880ac9A755fd29B2688956BD959F933F8 \
  --swap-type buy
```

### High-level: swap EVM (create + sign + send)

Requires `AVE_EVM_PRIVATE_KEY` or `AVE_MNEMONIC`, plus a user-provided RPC node via `--rpc-url` or `AVE_BSC_RPC_URL` / `AVE_ETH_RPC_URL` / `AVE_BASE_RPC_URL`.
The CLI uses that RPC only for local signing metadata (nonce, gas price, gas estimate) and submits the signed transaction through Ave's `sendSignedEvmTx` API.

```bash
python scripts/ave_trade_rest.py swap-evm \
  --chain bsc \
  --rpc-url https://your-bsc-rpc.example \
  --in-amount 1000000000000000000 \
  --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee \
  --out-token 0xb4357054c3da8d46ed642383f03139ac7f090343 \
  --swap-type buy \
  --slippage 500 \
  [--auto-slippage] \
  [--use-mev] \
  [--fee-recipient 0x...] \
  [--fee-recipient-rate 50]
```

### High-level: swap Solana (create + sign + send)

Requires `AVE_SOLANA_PRIVATE_KEY` or `AVE_MNEMONIC`.

```bash
python scripts/ave_trade_rest.py swap-solana \
  --in-amount 1000000 \
  --in-token sol \
  --out-token 4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R \
  --swap-type buy \
  --slippage 500 \
  --fee 50000000 \
  [--auto-slippage] \
  [--use-mev] \
  [--fee-recipient ...] \
  [--fee-recipient-rate 100]
```

### Low-level: create EVM transaction (external signer workflow)

```bash
python scripts/ave_trade_rest.py create-evm-tx \
  --chain bsc \
  --creator-address 0x... \
  --in-amount 1000000 \
  --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee \
  --out-token 0xb4357... \
  --swap-type buy \
  --slippage 500
```

Returns `requestTxId` and `txContent` for external signing.

### Low-level: send signed EVM transaction

```bash
python scripts/ave_trade_rest.py send-evm-tx \
  --chain bsc \
  --request-tx-id 123456789 \
  --signed-tx 0xd6af... \
  [--use-mev]
```

### Low-level: create Solana transaction (external signer workflow)

```bash
python scripts/ave_trade_rest.py create-solana-tx \
  --creator-address EgsEi74... \
  --in-amount 1000000 \
  --in-token sol \
  --out-token 4k3Dyjz... \
  --swap-type buy \
  --slippage 500 \
  --fee 50000000
```

Returns `requestTxId` and `txContent` (base64 message) for external signing.

### Low-level: send signed Solana transaction

```bash
python scripts/ave_trade_rest.py send-solana-tx \
  --request-tx-id ddee4ce0... \
  --signed-tx ATINUByp... \
  [--use-mev]
```

## Response Contract

After every chain-wallet action, answer in this order:

1. Outcome: quote created, tx created, tx submitted, or tx confirmed
2. Spend and fee impact: input amount, gas / fee, and any server-applied slippage difference
3. Identifiers: `requestTxId`, tx hash, and chain
4. Next step: sign, send, confirm, approve, or sell back

If a sell path requires approval, say that explicitly before retrying.

## Error Translation

Map common failures into clear next actions:

| Raw issue pattern | User-facing explanation |
|---|---|
| missing API key / auth failed | credentials are missing or invalid; check `AVE_API_KEY` |
| `Invalid parameter: feeRecipientRate` with only `feeRecipient` set | pair `feeRecipient` with `feeRecipientRate`, or remove both |
| missing signing envs | set `AVE_MNEMONIC` or the per-chain private key env |
| RPC required for `swap-evm` | provide `--rpc-url` or set the chain-specific RPC env |
| RPC connection refused / timeout | the RPC endpoint is unreachable; try a different RPC URL |
| insufficient token balance / insufficient gas | fund the wallet with the spend token or native gas token |
| approval required | approve the token first, then retry the sell |
| transaction reverted / execution failed | the on-chain tx failed; check slippage, gas, or token tax |
| route too small / min notional failure | the trade size is below the route minimum; increase size slightly |
| HTTP 200 with JSON error status | treat it as a failed API call, not a success |
| `gasLimit` returned as 0 | the CLI auto-estimates gas with 1.3x buffer; if it still fails, increase gas manually |

Prefer the translated explanation first, then include the raw API message if it helps debugging.

## Response Templates

- Quote:
  `Quote ready: <input token/amount> -> <estimated output>. Notes: <route/slippage>. Next: create tx or adjust size.`
- Create tx:
  `Transaction created: <chain> <swap type>. Spend: <input>, applied slippage: <value>, requestTxId: <id>. Next: sign locally and send.`
- Send / confirm:
  `Transaction submitted: <tx hash>. Spend: <input>, fee/gas: <value>. Next: confirm receipt or prepare sell-back.`

## Trading Parameter Reference

| Parameter | Type | Description |
|---|---|---|
| `--slippage` | integer (bps) | Max slippage tolerance. `500` = 5%, `1000` = 10%. Required on all create/swap commands |
| `--auto-slippage` | flag | Let the API auto-adjust slippage based on token volatility. Overrides `--slippage` value |
| `--use-mev` | flag | Enable MEV protection (front-running bundling). Recommended for large trades |
| `--fee` | integer (lamports) | Solana priority fee. `50000000` = 0.05 SOL. Required on Solana create/swap commands |
| `--fee-recipient` | address | Wallet address to receive trading fee rebate. Must be paired with `--fee-recipient-rate` |
| `--fee-recipient-rate` | integer (bps) | Rebate ratio, max 1000 (10%). E.g. `100` = 1% rebate. Must be paired with `--fee-recipient` |
| `--rpc-url` | URL | EVM JSON-RPC endpoint for local signing (nonce, gas estimate). Required for `swap-evm` |

**Units:**
- EVM amounts: wei (1 BNB = 10^18 wei, 1 USDT on BSC = 10^18 wei)
- Solana amounts: lamports (1 SOL = 10^9 lamports)
- Slippage/rates: basis points (1 bps = 0.01%)

## Signing Details

- **EVM**: uses `eth-account`; BIP44 path `m/44'/60'/0'/0/0` for mnemonic derivation
- **Solana**: uses `solders`; BIP44 path `m/44'/501'/0'/0'` for mnemonic derivation
- Individual key (`AVE_EVM_PRIVATE_KEY` / `AVE_SOLANA_PRIVATE_KEY`) takes priority over mnemonic

## Reference

See `references/trade-api-doc.md` → Chain Wallet Trading section.
