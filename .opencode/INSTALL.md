# Installing AVE Cloud Skills for OpenCode

Enable AVE Cloud skills in OpenCode via native skill discovery.

## Prerequisites

- Git
- AVE API key from [cloud.ave.ai](https://cloud.ave.ai)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AveCloud/ave-cloud-skill.git ~/.opencode/ave-cloud-skill
   ```

2. **Register the plugin:**

   ```bash
   mkdir -p ~/.opencode/plugins
   ln -s ~/.opencode/ave-cloud-skill ~/.opencode/plugins/ave-cloud-skill
   ```

3. **Link the skills:**

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.opencode/ave-cloud-skill/skills ~/.agents/skills/ave-cloud-skill
   ```

4. **Configure credentials in your shell session:**

   ```bash
   export AVE_API_KEY="<your_api_key>"
   export API_PLAN="free"
   ```

5. **Restart OpenCode** to discover the skills.

## Verify

After restarting, ask OpenCode which AVE Cloud skills are available. It should list the four skills from this repo.

## Available Skills

| Skill | When to Use |
|---|---|
| `ave-data-rest` | Token search, price, kline history, holders, txs, ranks, risk |
| `ave-data-wss` | Live price, tx, and kline streams; persistent WebSocket server |
| `ave-trade-chain-wallet` | Self-custody quote, create, sign, and send flows |
| `ave-trade-proxy-wallet` | Proxy-wallet market/limit orders, wallet management, order status |

## Updating

```bash
cd ~/.opencode/ave-cloud-skill && git pull
```

## Uninstalling

```bash
rm ~/.agents/skills/ave-cloud-skill
rm ~/.opencode/plugins/ave-cloud-skill
rm -rf ~/.opencode/ave-cloud-skill   # optional
```
