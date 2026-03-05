---
name: ave-trade-chain-wallet
version: 1.0.0
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

Requires `AVE_EVM_PRIVATE_KEY` or `AVE_MNEMONIC`.

```bash
python scripts/ave_trade_rest.py swap-evm \
  --chain bsc \
  --in-amount 1000000000000000000 \
  --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee \
  --out-token 0xb4357054c3da8d46ed642383f03139ac7f090343 \
  --swap-type buy \
  --slippage 500 \
  [--auto-slippage] \
  [--use-mev] \
  [--fee-recipient 0x...]
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
  [--fee-recipient ...]
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

## Signing Details

- **EVM**: uses `eth-account`; BIP44 path `m/44'/60'/0'/0/0` for mnemonic derivation
- **Solana**: uses `solders`; BIP44 path `m/44'/501'/0'/0'` for mnemonic derivation
- Individual key (`AVE_EVM_PRIVATE_KEY` / `AVE_SOLANA_PRIVATE_KEY`) takes priority over mnemonic

## Reference

See `references/trade-api-doc.md` → Chain Wallet Trading section.
