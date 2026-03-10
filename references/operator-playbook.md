## AVE Operator Playbook

Use this reference when the request spans multiple AVE skills or when the agent needs one shared source for current operating rules.

### Trade Path Preference

- Prefer proxy-wallet trading over chain-wallet trading when both are acceptable.
- Use chain-wallet only when the user explicitly wants self-custody, local signing, mnemonic/private-key usage, or an external signer flow.
- For broad asks like "buy this token" or "help me trade this", start with proxy-wallet plus a small preflight.

### WSS Connection Discipline

- Prefer one reusable WebSocket connection with `subscribe` / `unsubscribe`.
- Treat 5 concurrent WSS connections as the practical ceiling for a single operator session.
- Reuse the REPL or Docker server daemon for multi-topic monitoring.
- If the user changes monitoring targets, unsubscribe old topics before opening more streams.
- For chat surfaces, summarize stream updates periodically instead of forwarding every event.

### Chat Surface Guidance

- OpenClaw: default to compact cards, short summaries, and ASCII mini-chart fallback.
- Claude: keep explanations clear, but still summarize raw payloads into user-facing decisions.
- Codex: prefer terse operator output with identifiers and next actions first.

### Client-Specific Defaults

| Client | Default |
|---|---|
| OpenClaw | compact token card, concise live summary, avoid wide tables, prefer one-screen updates |
| Claude | brief explanation plus decision, then identifiers and next action |
| Codex | shortest path to action, IDs and command-relevant output first |

### Token Link Pattern

When a token address and chain are known, include:

`https://pro.ave.ai/token/<token_address>-<chain>`

Example:

`https://pro.ave.ai/token/0x833679c9a3e0bb7258aa3a71162e2bd42bea4444-bsc`

### Current PROD Quirks

- Chain-wallet `feeRecipient` must be paired with `feeRecipientRate` on both EVM and Solana.
- EVM create responses can return an applied slippage value different from the requested slippage.
- Data WSS connection churn can trigger `Too Many Connections`; reuse connections instead of opening many fresh sockets.
- Solana route minimums can reject very small notionals; increase slightly only when the user-approved cap allows it.
- For high-level EVM `swap-evm`, a user RPC URL is required for local signing metadata.

### Common Recovery Rules

| Failure | Recovery |
|---|---|
| `Too Many Connections` | close extra WSS sessions, reuse the existing daemon or REPL, retry after reducing socket count |
| route too small | increase notional slightly or stop and explain the route minimum |
| approval required | perform approval first, then retry the spend or sell |
| proxy wallet unfunded | stop and ask for funding |
| RPC missing | request the user's RPC URL; do not fall back to public RPCs |
| token risk unclear | switch back to REST risk/liquidity checks before trading |

### Common State To Preserve

Carry these across turns when known:

- chain
- token or pair
- assetsId
- requestTxId
- proxy order ID
- tx hash
- spend cap
- test vs real
- active watch mode
