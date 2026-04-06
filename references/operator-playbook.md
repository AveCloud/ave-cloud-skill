## AVE Operator Playbook

Shared cross-skill operating rules. Individual reference files cover specific topics — see links below.

### See Also

- [error-translation.md](error-translation.md) — unified error table
- [safe-test-defaults.md](safe-test-defaults.md) — per-chain test caps
- [token-conventions.md](token-conventions.md) — address rules, trading params, signing
- [response-contract.md](response-contract.md) — response templates, state handoff, recovery
- [presentation-guide.md](presentation-guide.md) — output formatting and card templates
- [learn-more.md](learn-more.md) — AVE links and cloud registration

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

| Client | Default |
|---|---|
| OpenClaw | Compact token card, concise live summary, avoid wide tables, prefer one-screen updates |
| Claude | Brief explanation plus decision, then identifiers and next action |
| Codex | Shortest path to action, IDs and command-relevant output first |

### Token Link Pattern

When a token address and chain are known, include:

`https://pro.ave.ai/token/<token_address>-<chain>`

### Current PROD Quirks

- Chain-wallet `feeRecipient` must be paired with `feeRecipientRate` on both EVM and Solana.
- EVM create responses can return an applied slippage value different from the requested slippage.
- Data WSS connection churn can trigger `Too Many Connections`; reuse connections instead of opening many fresh sockets.
- Solana route minimums can reject very small notionals; increase slightly only when the user-approved cap allows it.
- For high-level EVM `swap-evm`, a user RPC URL is required for local signing metadata.
