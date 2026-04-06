# Token and Address Conventions

## Address Rules

| Topic | Convention |
|---|---|
| EVM native token placeholder | `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` |
| Solana native token input | `sol` |
| Token search identifiers | Prefer `contract-chain` for batch price and live price subscriptions |
| EVM addresses in user output | Preserve the chain's normal display style; lowercase only when the API requires it |
| Solana identifiers | Use mint or wallet addresses exactly as provided; do not lowercase |
| Wrapped/native distinction | `WBNB` is a token, `BNB` is the native coin — treat carefully in explanations |

## Fee Pairing Rule

Pair `feeRecipient` with `feeRecipientRate` on both EVM and Solana if you set either. Unpaired `feeRecipient` produces errors in PROD.

## Common Test Fixtures

| Chain | Token | Address / Symbol |
|---|---|---|
| BSC | USDT | `0x55d398326f99059fF775485246999027B3197955` |
| BSC | BTCB | `0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c` |
| BSC | WBNB | `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` |
| Solana | SOL | `sol` |
| Solana | USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |

## Trading Parameters

| Parameter | Type | Description |
|---|---|---|
| `--slippage` | integer (bps) | Max slippage tolerance. `500` = 5%, `1000` = 10%. Required on all create/swap commands |
| `--auto-slippage` | flag | Let API auto-adjust slippage based on token volatility. Overrides `--slippage` value |
| `--use-mev` | flag | Enable MEV protection (front-running bundling). Recommended for large trades |
| `--gas` | string | Manual gas/priority fee in smallest unit (wei for EVM, lamports for Solana) |
| `--extra-gas` | string | Additional gas on top of estimated amount |
| `--auto-gas` | `low` / `average` / `high` | Auto gas estimation tier. Recommended: `average` |
| `--fee` | integer (lamports) | Solana priority fee. `50000000` = 0.05 SOL. Required on Solana create/swap commands |
| `--fee-recipient` | address | Wallet to receive trading fee rebate. Must pair with `--fee-recipient-rate` |
| `--fee-recipient-rate` | integer (bps) | Rebate ratio, max 1000 (10%). Must pair with `--fee-recipient` |
| `--limit-price` | float (USD) | Target price for limit orders |
| `--expire-time` | integer (seconds) | Limit order expiry. `86400` = 24 hours |

## Units

- EVM amounts: wei (1 BNB = 10^18 wei, 1 USDT on BSC = 10^18 wei)
- Solana amounts: lamports (1 SOL = 10^9 lamports)
- Slippage/rates: basis points (1 bps = 0.01%)

## Signing Details

- **EVM**: uses `eth-account`; BIP44 path `m/44'/60'/0'/0/0` for mnemonic derivation
- **Solana**: uses `solders`; BIP44 path `m/44'/501'/0'/0'` for mnemonic derivation
- Individual key (`AVE_EVM_PRIVATE_KEY` / `AVE_SOLANA_PRIVATE_KEY`) takes priority over mnemonic
