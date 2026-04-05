# AVE Cloud Skills

Ave Cloud 技能套件，用于通过 Ave Cloud API (https://cloud.ave.ai) 查询链上加密数据并执行 DEX 交易。支持 BSC、Solana、ETH 和 Base。

## 为什么选择 AVE Cloud Skills

- 实时多链数据（BSC、Solana、ETH、Base）
- 支持 self-custody chain-wallet 和 server-managed proxy-wallet 交易
- 提供价格、交易和 kline 数据的实时 WebSocket 流
- 内置风险检测和 honeypot 安全检查

## 技能

| Skill | Script | 适用场景 |
|---|---|---|
| ave-data-rest | ave_data_rest.py | Token 搜索、价格、kline、holders、swap txs、trending、risk |
| ave-data-wss | ave_data_wss.py | 实时价格/tx/kline 流、WSS REPL、server daemon（需要 API_PLAN=pro） |
| ave-trade-chain-wallet | ave_trade_rest.py | self-custody DEX 交易，用户自行控制私钥 |
| ave-trade-proxy-wallet | ave_trade_rest.py, ave_trade_wss.py | market/limit orders、TP/SL、proxy wallet 管理（需要 API_PLAN=normal 或 pro） |
| ave-wallet-suite | (router) | 将不明确的钱包、交易或数据请求路由到正确的子技能 |

## 快速开始

先构建本地 Docker image：

```bash
docker build -f scripts/Dockerfile.txt -t ave-cloud .
```

### Token 搜索

```bash
docker run --rm \
  -e AVE_API_KEY=your_api_key_here \
  -e API_PLAN=free \
  --entrypoint python3 \
  ave-cloud scripts/ave_data_rest.py search --keyword PEPE
```

### 实时监看

```bash
docker run --rm -it \
  -e AVE_API_KEY=your_api_key_here \
  -e API_PLAN=pro \
  --entrypoint python3 \
  ave-cloud scripts/ave_data_wss.py wss-repl
```

### Dry-Run 交易预览

```bash
docker run --rm \
  -e AVE_API_KEY=your_api_key_here \
  -e API_PLAN=free \
  --entrypoint python3 \
  ave-cloud scripts/ave_trade_rest.py quote \
  --chain bsc \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 \
  --swap-type buy
```

## 安装

### 安装矩阵

| 客户端 | 安装方式 | 配置目录 |
|---|---|---|
| Claude Code | plugin discovery | .claude-plugin/ |
| Codex | clone + symlink | .codex/ |
| Cursor | plugin discovery | .cursor-plugin/ |
| OpenCode | clone + symlink | .opencode/ |
| OpenClaw | clone + symlink | .openclaw/ |

本仓库当前包含 `.claude-plugin/`、`.codex/`、`.cursor-plugin/` 和 `.opencode/`。
如果你维护对应的 `.openclaw/` 目录，可以沿用同样的 clone + symlink 方式。

### API Plan 矩阵

| 功能 | free | normal | pro |
|---|---|---|---|
| Data REST | Yes | Yes | Yes |
| Data WSS | No | No | Yes |
| Trade Chain-Wallet | Yes | Yes | Yes |
| Trade Proxy-Wallet | No | Yes | Yes |

在 https://cloud.ave.ai 获取你的 API key

## 支持的链

Data REST 和 Data WSS 实际覆盖更多链，但本仓库中的完整交易流程主要聚焦以下四条链。

| Chain | Data | Chain-Wallet | Proxy-Wallet |
|---|---|---|---|
| BSC | Yes | Yes | Yes |
| Solana | Yes | Yes | Yes |
| ETH | Yes | Yes | Yes |
| Base | Yes | Yes | Yes |

## 环境变量

| 变量 | 适用技能 | 说明 |
|---|---|---|
| AVE_API_KEY | all skills | 来自 https://cloud.ave.ai 的 Ave Cloud API key |
| API_PLAN | all skills | free / normal / pro |
| AVE_SECRET_KEY | trade-proxy-wallet | proxy wallet 认证使用的 HMAC signing secret |
| AVE_EVM_PRIVATE_KEY | trade-chain-wallet (optional) | 用于 BSC/ETH/Base 签名的十六进制私钥 |
| AVE_SOLANA_PRIVATE_KEY | trade-chain-wallet (optional) | 用于 Solana 签名的 Base58 私钥 |
| AVE_MNEMONIC | trade-chain-wallet (optional) | 适用于所有链的 BIP39 mnemonic |
| AVE_USE_DOCKER | all scripts | 设为 true 以启用基于 Docker 的执行和 Docker rate limiting |
| AVE_BSC_RPC_URL | trade-chain-wallet (optional) | 覆盖 BSC JSON-RPC URL |
| AVE_ETH_RPC_URL | trade-chain-wallet (optional) | 覆盖 ETH JSON-RPC URL |
| AVE_BASE_RPC_URL | trade-chain-wallet (optional) | 覆盖 Base JSON-RPC URL |

## Token Links

在 AVE Pro 查看 Token 详情：`https://pro.ave.ai/token/<token>-<chain>`

示例：`https://pro.ave.ai/token/0x1234...abcd-bsc`

## 许可证

MIT
