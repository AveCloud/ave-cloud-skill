# Safe Test Defaults

Use these defaults for first real tests unless the user gives stricter limits.

## Per-Chain Defaults

| Chain | Wallet type | Default test input | Cap guidance |
|---|---|---|---|
| BSC | chain-wallet | `0.0005 BNB` | Keep gas under `0.0003 BNB`; abort if route or gas spikes |
| BSC | proxy-wallet | `0.0005 BNB` | Verify funded wallet and sell back promptly |
| Solana | chain-wallet | `0.0005 SOL` | Keep total fee budget under `0.0005 SOL`; abort if higher |
| Solana | proxy-wallet | start at `0.002 SOL` if smaller sizes fail | Prefer smallest accepted route size |

## Rules

- Always surface the spend cap to the user before the real test starts.
- Abort or fall back to create-only preview if the route exceeds the caps above.
- Use a disposable proxy wallet for testing when possible.
- After a test buy confirms, prefer an immediate sell-back instead of leaving exposure open.
- If the proxy wallet is unfunded, stop and ask for funding before submitting the order.
