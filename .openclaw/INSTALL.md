# Installing AVE Cloud Skills for OpenClaw

Enable AVE Cloud skills in OpenClaw via native skill discovery.

## Prerequisites

- Git
- AVE API key from [cloud.ave.ai](https://cloud.ave.ai)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AveCloud/ave-cloud-skill.git ~/.openclaw/ave-cloud-skill
   ```

2. **Create the skills symlink:**

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.openclaw/ave-cloud-skill/skills ~/.agents/skills/ave-cloud-skill
   ```

   **Windows (PowerShell):**

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\ave-cloud-skill" "$env:USERPROFILE\.openclaw\ave-cloud-skill\skills"
   ```

3. **Configure credentials in your shell session:**

   ```bash
   export AVE_API_KEY="your_api_key_here"
   export API_PLAN="free"
   ```

4. **Restart OpenClaw** to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/ave-cloud-skill
```

You should see four skill directories: `data-rest`, `data-wss`, `trade-chain-wallet`, and `trade-proxy-wallet`.

## Available Skills

| Skill | When to Use |
|---|---|
| `ave-data-rest` | Token search, price, kline history, holders, txs, ranks, risk |
| `ave-data-wss` | Live price, tx, and kline streams; persistent WebSocket server |
| `ave-trade-chain-wallet` | Self-custody quote, create, sign, and send flows |
| `ave-trade-proxy-wallet` | Proxy-wallet market/limit orders, wallet management, order status |

## Updating

```bash
cd ~/.openclaw/ave-cloud-skill && git pull
```

## Uninstalling

```bash
rm ~/.agents/skills/ave-cloud-skill
rm -rf ~/.openclaw/ave-cloud-skill   # optional
```
