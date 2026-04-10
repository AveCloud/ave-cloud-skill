---
name: ave-trade-chain-wallet
version: 2.4.0
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
  - Generic buy/sell/swap/limit order requests without explicit self-custody language → use ave-trade-proxy-wallet instead
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

Self-custody DEX trading via the AVE Cloud Chain Wallet API. Use this only when the user explicitly wants local signing, private-key or mnemonic control, or an external signer workflow. For shared trade-path rules and current PROD quirks, see [operator-playbook.md](../../references/operator-playbook.md).

**Trading fee:** 0.6% | **Rebate to `feeRecipient`:** 20%

## Route Cues

| EN | ZH |
|---|---|
| "use my private key", "sign with my key" | "用我的私钥", "用私钥签名" |
| "use my mnemonic", "use my seed phrase" | "用我的助记词", "用种子短语" |
| "sign locally", "self-custody" | "本地签名", "自托管" |
| "use my own wallet" | "用我自己的钱包" |
| "build an unsigned tx", "external signer" | "构建未签名交易", "外部签名" |

## Setup

```bash
export AVE_API_KEY="your_api_key_here"
export API_PLAN="free"   # free | normal | pro
export AVE_EVM_PRIVATE_KEY="0x..."         # optional for EVM signed send
export AVE_SOLANA_PRIVATE_KEY="base58..."  # optional for Solana signed send
export AVE_MNEMONIC="word1 word2 ... word12"  # optional fallback
```

Get a key at https://cloud.ave.ai/register. EVM signed sends also require `--rpc-url` or `AVE_BSC_RPC_URL` / `AVE_ETH_RPC_URL` / `AVE_BASE_RPC_URL`.

## Rate Limits

| `API_PLAN` | Write TPS |
|---|---|
| `free` | 1 |
| `normal` | 5 |
| `pro` | 20 |

## Supported Chains

`bsc`, `eth`, `base`, `solana`

Preview or create first, then submit only after the path is valid and the user has confirmed execution.

## Common Pitfalls

- **Solana native token**: Use `sol` (not `So11111111111111111111111111111111111111112`) for `--in-token` / `--out-token` in all trade commands. The full mint address is rejected by the API.
- **EVM sell requires approval first**: Before selling an ERC-20 token, run `approve-chain` to approve the swap router. Native coin buys do not need approval. Without approval, `swap-evm` sell will fail with `status 3025: failed to simulate send signed tx`.
- **Minimum swap value**: The API rejects swaps below ~$0.10 USD with `swap value too small`. Use at least 0.01 SOL / 0.001 BNB / 0.0001 ETH.
- **Solana fee required**: `swap-solana` and `create-solana-tx` require `--fee` (lamports). With `--use-mev`, minimum is 1000000 (0.001 SOL). Use `gas-tip` to query recommended values.
- **EVM RPC required**: `swap-evm` requires `--rpc-url` or the chain env var (`AVE_BSC_RPC_URL`, etc.) for local signing (nonce, gas price, estimate gas).
- **Query slippage first**: Use `auto-slippage` to get the recommended slippage for a token before trading. The API may override your slippage value.

## Operations

### Quote

Get estimated output before building or sending anything. Response includes `spender` field for approval.

```bash
python scripts/ave_trade_rest.py quote --chain <chain> --in-amount <amount> --in-token <token> --out-token <token> --swap-type buy|sell
```

### Auto Slippage

Query recommended slippage (bps) for a token before trading.

```bash
python scripts/ave_trade_rest.py auto-slippage --chain <chain> --token <token_address> [--use-mev]
```

### Gas Tip

Query recommended gas prices per chain. Returns low/average/high tiers in lamports (Solana) or wei (EVM).

```bash
python scripts/ave_trade_rest.py gas-tip
```

### Approve Chain (EVM only)

Approve an ERC-20 token for the swap router before selling. Not needed for native coin buys. Gets spender from quote, builds and signs approve(MAX_UINT256) tx locally.

```bash
python scripts/ave_trade_rest.py approve-chain --chain bsc --token <erc20_address> [--rpc-url https://...]
```

### Swap EVM

Create, sign, and send an EVM swap locally with a key or mnemonic.

```bash
python scripts/ave_trade_rest.py swap-evm --chain bsc --rpc-url https://... --in-amount <amount> --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee --out-token <token> --swap-type buy --slippage 500 [--auto-slippage] [--use-mev]
```

### Swap Solana

Create, sign, and send a Solana swap locally with a key or mnemonic.

```bash
python scripts/ave_trade_rest.py swap-solana --in-amount <amount> --in-token sol --out-token <token> --swap-type buy --slippage 500 --fee 50000000 [--auto-slippage] [--use-mev]
```

### Create EVM tx

Build an unsigned EVM swap transaction for an external signer.

```bash
python scripts/ave_trade_rest.py create-evm-tx --chain bsc --creator-address 0x... --in-amount <amount> --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee --out-token <token> --swap-type buy --slippage 500
```

### Send EVM tx

Submit a pre-signed EVM transaction returned from `create-evm-tx`.

```bash
python scripts/ave_trade_rest.py send-evm-tx --chain bsc --request-tx-id <id> --signed-tx 0x...
```

### Create Solana tx

Build an unsigned Solana swap transaction for an external signer.

```bash
python scripts/ave_trade_rest.py create-solana-tx --creator-address <wallet> --in-amount <amount> --in-token sol --out-token <token> --swap-type buy --slippage 500 --fee 50000000
```

### Send Solana tx

Submit a pre-signed Solana transaction returned from `create-solana-tx`.

```bash
python scripts/ave_trade_rest.py send-solana-tx --request-tx-id <id> --signed-tx <signed_tx>
```

## Workflow Examples

### EVM buy + sell flow (self-custody)

Buy a token, then approve and sell it back. Approval is only needed once per token per spender.

```bash
# 1. Check gas and slippage
python scripts/ave_trade_rest.py gas-tip
python scripts/ave_trade_rest.py auto-slippage --chain bsc --token <token>

# 2. Buy (native coin -> token, no approval needed)
python scripts/ave_trade_rest.py swap-evm --chain bsc --in-amount 1000000000000000 --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee --out-token <token> --swap-type buy --slippage 1000

# 3. Approve token for selling (one-time per token)
python scripts/ave_trade_rest.py approve-chain --chain bsc --token <token>

# 4. Sell (token -> native coin)
python scripts/ave_trade_rest.py swap-evm --chain bsc --in-amount <amount> --in-token <token> --out-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee --swap-type sell --slippage 1000
```

### Solana buy + sell flow (self-custody)

No approval needed on Solana. Use `sol` for native token.

```bash
# Buy
python scripts/ave_trade_rest.py swap-solana --in-amount 10000000 --in-token sol --out-token <token> --swap-type buy --slippage 1000 --fee 1000000 --use-mev

# Sell (use full token address for in-token, sol for out-token)
python scripts/ave_trade_rest.py swap-solana --in-amount <amount> --in-token <token_address> --out-token sol --swap-type sell --slippage 1000 --fee 1000000 --use-mev
```

### External signer EVM flow

Preview first, then build the unsigned transaction, then submit the signed payload.

```bash
python scripts/ave_trade_rest.py quote --chain bsc --in-amount 500000000000000 --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee --out-token <token> --swap-type buy
python scripts/ave_trade_rest.py create-evm-tx --chain bsc --creator-address 0x... --in-amount 500000000000000 --in-token 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee --out-token <token> --swap-type buy --slippage 500
python scripts/ave_trade_rest.py send-evm-tx --chain bsc --request-tx-id <id> --signed-tx 0x...
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
