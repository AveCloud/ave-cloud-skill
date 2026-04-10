"""Interactive async WebSocket REPL."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from ave.config import WSS_BASE, get_api_key, get_api_plan


async def cmd_wss_repl(args: argparse.Namespace) -> None:
    if get_api_plan() != "pro":
        print("Error: WebSocket subscriptions require API_PLAN=pro.", file=sys.stderr)
        sys.exit(1)

    import websockets
    headers = {"X-API-KEY": get_api_key()}
    msg_id = 0

    async with websockets.connect(WSS_BASE, additional_headers=headers) as ws:
        print("Connected. Type 'help' for commands.", file=sys.stderr)

        async def _reader() -> None:
            async for message in ws:
                try:
                    print(json.dumps(json.loads(message), indent=2), flush=True)
                except json.JSONDecodeError:
                    print(message, flush=True)
                print("---", flush=True)

        read_task = asyncio.create_task(_reader())
        loop = asyncio.get_event_loop()

        try:
            while True:
                try:
                    line = await loop.run_in_executor(None, input, "\n> ")
                except EOFError:
                    break
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                cmd = parts[0].lower()
                if cmd in ("quit", "exit", "q"):
                    break
                elif cmd == "help":
                    print("Commands:\n  subscribe price <addr-chain> [...]\n  subscribe tx <pair> <chain> [tx|multi_tx|liq]\n  subscribe kline <pair> <chain> [interval]\n  unsubscribe\n  quit", file=sys.stderr)
                elif cmd == "subscribe" and len(parts) >= 2:
                    msg_id += 1
                    topic = parts[1]
                    if topic == "price" and len(parts) >= 3:
                        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": ["price", parts[2:]], "id": msg_id}))
                    elif topic in ("tx", "multi_tx", "liq") and len(parts) >= 4:
                        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": [topic, parts[2], parts[3]], "id": msg_id}))
                    elif topic == "kline" and len(parts) >= 4:
                        iv = parts[4] if len(parts) > 4 else "k60"
                        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": ["kline", parts[2], iv, parts[3]], "id": msg_id}))
                    else:
                        print(f"Unknown topic: {topic!r}. Topics: price, tx, multi_tx, liq, kline", file=sys.stderr)
                elif cmd == "unsubscribe":
                    msg_id += 1
                    await ws.send(json.dumps({"jsonrpc": "2.0", "method": "unsubscribe", "params": [], "id": msg_id}))
                else:
                    print(f"Unknown command: {cmd!r}. Type 'help'.", file=sys.stderr)
        except KeyboardInterrupt:
            pass
        finally:
            read_task.cancel()
