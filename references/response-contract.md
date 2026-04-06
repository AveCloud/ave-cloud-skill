# Response Contract

## Priority Order

When reporting an action result, use this order unless the user explicitly wants raw payloads first:

1. Outcome — what happened
2. Spend / fees / slippage — what it cost
3. Identifiers — requestTxId, order ID, tx hash
4. Next action — what to do next

## Preview Wording Rule

When presenting a trade preview or dry-run, never say "not executed" or "has not been executed". Use "pending confirmation", "not yet submitted", or "preview only — no trade has been placed" instead. The word "executed" should only appear when a trade has actually been confirmed on-chain.

## Agent Behavior Modes

Adjust response style to the client surface:

| Mode | Use when | Output style |
|---|---|---|
| terse operator | Codex / terminal / highly technical user | Identifiers first, short status, minimal prose |
| guided beginner | First-time user or unclear intent | Explain next action and main tradeoff in plain language |
| chat-first mobile | OpenClaw / Telegram-like chat surfaces | Compact cards, short paragraphs, avoid wide tables |

Prefer `chat-first mobile` for OpenClaw unless the user explicitly asks for raw payloads.

## State Handoff

Carry these fields forward explicitly across turns when known:

- `chain`
- `token` / `pair`
- `assetsId`
- `requestTxId`
- proxy order ID
- tx hash
- spend cap
- test vs real
- active watch mode

When switching skills or phases, restate currently known state before taking the next action.

## Response Templates

### Data skills

- **Token search**: one primary token card, then compact alternates if needed
- **Risk check**: `risk level -> key flags -> tax/owner/honeypot notes -> next action`
- **Quote**: `pair -> input -> estimated output -> route notes -> next action`
- **Live watch update**: `what changed -> key number(s) -> direction -> next watch action`

### Trade skills

- **Quote**: `Quote ready: <input token/amount> -> <estimated output>. Notes: <route/slippage>. Next: create tx or adjust size.`
- **Create tx**: `Transaction created: <chain> <swap type>. Spend: <input>, applied slippage: <value>, requestTxId: <id>. Next: sign locally and send.`
- **Send / confirm**: `Transaction submitted: <tx hash>. Spend: <input>, fee/gas: <value>. Next: confirm receipt or prepare sell-back.`
- **Wallet create**: `Proxy wallet created: <assetsId> on <supported chains>. Next: fund the wallet or place a test order.`
- **Market order**: `Order submitted: <chain> <buy/sell> via proxy wallet <assetsId>. Spend: <amount/token>. IDs: <order id>. Next: watch orders or poll status.`
- **Limit order**: `Limit order placed: trigger price <value>. IDs: <order id>. Next: monitor or cancel if conditions change.`
- **Order confirmation**: `Order confirmed: <order id>, tx hash <hash>. Spend/result: <summary>. Next: sell back, monitor, or clean up the wallet.`

## Failure Recovery Playbook

When a step fails, prefer the smallest safe recovery:

| Failure | Recovery |
|---|---|
| WSS connection limit hit | Close extra sessions, reuse existing daemon or REPL, retry after reducing socket count |
| Route too small | Increase notional slightly or stop and explain the route minimum |
| Approval required | Perform approval first, then retry the spend or sell |
| Proxy wallet unfunded | Stop and ask for funding |
| RPC missing | Request user's RPC URL; do not fall back to public RPCs |
| Token risk unclear | Switch back to REST risk/liquidity checks before trading |
