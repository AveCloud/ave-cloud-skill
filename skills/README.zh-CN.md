# AVE Cloud Skills 目录

## 概述
此目录包含 AVE Cloud API suite 的 5 个 skills。

## Skills

### ave-wallet-suite
- 类型: Router skill
- 描述: 将模糊的 wallet、trade 和 data 请求路由到正确的 sub-skill
- API Plan: free（仅 routing）

### ave-data-rest
- 类型: Data query
- 描述: Token 搜索、price、kline/OHLCV、holders、swap txs、trending、risk/honeypot checks
- API Plan: free / normal / pro
- Script: scripts/ave_data_rest.py

### ave-data-wss
- 类型: Real-time streaming
- 描述: 用于 live price、transaction 和 kline data 的 WebSocket streams
- API Plan: 仅 pro
- Script: scripts/ave_data_wss.py

### ave-trade-chain-wallet
- 类型: Self-custody trading
- 描述: Quote、build、sign 并发送 EVM/Solana transactions。用户控制 private keys。
- API Plan: free / normal / pro
- Script: scripts/ave_trade_rest.py

### ave-trade-proxy-wallet
- 类型: Server-managed trading
- 描述: Market/limit orders、TP/SL、proxy wallet management、order status monitoring
- API Plan: normal / pro
- Script: scripts/ave_trade_rest.py, scripts/ave_trade_wss.py

## 环境变量

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

## API Plan 矩阵

| Feature | free | normal | pro |
|---------|------|--------|-----|
| Data REST | yes | yes | yes |
| Data WSS | no | no | yes |
| Trade Chain-Wallet | yes | yes | yes |
| Trade Proxy-Wallet | no | yes | yes |

## 参考资料
- Data API: references/data-api-doc.md
- Trade API: references/trade-api-doc.md
- Operator Playbook: references/operator-playbook.md
