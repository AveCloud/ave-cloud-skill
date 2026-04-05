# 为 OpenCode 安装 AVE Cloud Skills

通过原生 skill discovery 在 OpenCode 中启用 AVE Cloud skills。

## 前置要求

- Git
- 来自 [cloud.ave.ai](https://cloud.ave.ai) 的 AVE API key

## 安装

1. **Clone 仓库:**

   ```bash
   git clone https://github.com/AveCloud/ave-cloud-skill.git ~/.opencode/ave-cloud-skill
   ```

2. **注册 plugin:**

   ```bash
   mkdir -p ~/.opencode/plugins
   ln -s ~/.opencode/ave-cloud-skill ~/.opencode/plugins/ave-cloud-skill
   ```

3. **链接 skills:**

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.opencode/ave-cloud-skill/skills ~/.agents/skills/ave-cloud-skill
   ```

4. **在你的 shell session 中配置 credentials:**

   ```bash
   export AVE_API_KEY="your_api_key_here"
   export API_PLAN="free"
   ```

5. **重启 OpenCode** 以发现这些 skills。

## 验证

重启后，询问 OpenCode 当前有哪些可用的 AVE Cloud skills。它应该会列出这个仓库中的四个 skills。

## 可用 Skills

| Skill | 使用场景 |
|---|---|
| `ave-data-rest` | 用于 Token search、price、kline history、holders、txs、ranks、risk |
| `ave-data-wss` | 用于实时 price、tx 和 kline streams；持久化 WebSocket server |
| `ave-trade-chain-wallet` | 用于 self-custody 的 quote、create、sign 和 send 流程 |
| `ave-trade-proxy-wallet` | 用于 proxy-wallet 的 market/limit orders、wallet management、order status |

## 更新

```bash
cd ~/.opencode/ave-cloud-skill && git pull
```

## 卸载

```bash
rm ~/.agents/skills/ave-cloud-skill
rm ~/.opencode/plugins/ave-cloud-skill
rm -rf ~/.opencode/ave-cloud-skill   # optional
```
