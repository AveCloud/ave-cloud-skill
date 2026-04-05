# AVE Cloud Skills Catalog

## Overview
This directory contains 5 skills for the AVE Cloud API suite.

## Skills

### ave-wallet-suite
- Type: Router skill
- Description: Routes ambiguous wallet, trade, and data requests to the correct sub-skill
- API Plan: free (routing only)

### ave-data-rest
- Type: Data query
- Description: Token search, price, kline/OHLCV, holders, swap txs, trending, risk/honeypot checks
- API Plan: free / normal / pro
- Script: scripts/ave_data_rest.py

### ave-data-wss
- Type: Real-time streaming
- Description: WebSocket streams for live price, transaction, and kline data
- API Plan: pro only
- Script: scripts/ave_data_wss.py

### ave-trade-chain-wallet
- Type: Self-custody trading
- Description: Quote, build, sign, and send EVM/Solana transactions. User controls private keys.
- API Plan: free / normal / pro
- Script: scripts/ave_trade_rest.py

### ave-trade-proxy-wallet
- Type: Server-managed trading
- Description: Market/limit orders, TP/SL, proxy wallet management, order status monitoring
- API Plan: normal / pro
- Script: scripts/ave_trade_rest.py, scripts/ave_trade_wss.py

## Environment Variables

| Variable | Required by | Description |
|---|---|---|
| `AVE_API_KEY` | all skills | Ave Cloud API key from https://cloud.ave.ai |
| `API_PLAN` | all skills | `free` / `normal` / `pro` |
| `AVE_SECRET_KEY` | trade-proxy-wallet | HMAC signing secret for proxy wallet auth |
| `AVE_EVM_PRIVATE_KEY` | trade-chain-wallet (optional) | Hex private key for BSC/ETH/Base signing |
| `AVE_SOLANA_PRIVATE_KEY` | trade-chain-wallet (optional) | Base58 private key for Solana signing |
| `AVE_MNEMONIC` | trade-chain-wallet (optional) | BIP39 mnemonic for all chains; individual key takes priority |
| `AVE_USE_DOCKER` | all scripts | Set to `true` to use requests-ratelimiter (auto-set in Docker) |
| `AVE_BSC_RPC_URL` | trade-chain-wallet (optional) | Override BSC JSON-RPC URL (default: https://bsc.publicnode.com) |
| `AVE_ETH_RPC_URL` | trade-chain-wallet (optional) | Override ETH JSON-RPC URL (default: https://ethereum.publicnode.com) |
| `AVE_BASE_RPC_URL` | trade-chain-wallet (optional) | Override Base JSON-RPC URL (default: https://base.publicnode.com) |

## API Plan Matrix

| Feature | free | normal | pro |
|---------|------|--------|-----|
| Data REST | yes | yes | yes |
| Data WSS | no | no | yes |
| Trade Chain-Wallet | yes | yes | yes |
| Trade Proxy-Wallet | no | yes | yes |

## References
- Data API: references/data-api-doc.md
- Trade API: references/trade-api-doc.md
- Operator Playbook: references/operator-playbook.md
