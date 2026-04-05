# 为 Codex 安装 AVE Cloud Skills

通过原生 skill discovery 在 Codex 中启用 AVE Cloud skills。

## 前置要求

- Git
- 来自 [cloud.ave.ai](https://cloud.ave.ai) 的 AVE API key

## 安装

1. **Clone 仓库:**

   ```bash
   git clone https://github.com/AveCloud/ave-cloud-skill.git ~/.codex/ave-cloud-skill
   ```

2. **创建 skills 符号链接:**

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/ave-cloud-skill/skills ~/.agents/skills/ave-cloud-skill
   ```

   **Windows (PowerShell):**

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\ave-cloud-skill" "$env:USERPROFILE\.codex\ave-cloud-skill\skills"
   ```

3. **在你的 shell session 中配置 credentials:**

   ```bash
   export AVE_API_KEY="your_api_key_here"
   export API_PLAN="free"
   ```

4. **重启 Codex** 以发现这些 skills。

## 验证

```bash
ls -la ~/.agents/skills/ave-cloud-skill
```

你应该会看到四个 skill 目录：`data-rest`、`data-wss`、`trade-chain-wallet` 和 `trade-proxy-wallet`。

## 可用 Skills

| Skill | 使用场景 |
|---|---|
| `ave-data-rest` | 用于 Token search、price、kline history、holders、txs、ranks、risk |
| `ave-data-wss` | 用于实时 price、tx 和 kline streams；持久化 WebSocket server |
| `ave-trade-chain-wallet` | 用于 self-custody 的 quote、create、sign 和 send 流程 |
| `ave-trade-proxy-wallet` | 用于 proxy-wallet 的 market/limit orders、wallet management、order status |

## 更新

```bash
cd ~/.codex/ave-cloud-skill && git pull
```

## 卸载

```bash
rm ~/.agents/skills/ave-cloud-skill
rm -rf ~/.codex/ave-cloud-skill   # optional
```
