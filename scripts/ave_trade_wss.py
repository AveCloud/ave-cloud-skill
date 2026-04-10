#!/usr/bin/env python3
"""AVE Cloud Trade WebSocket client CLI."""

import argparse
import asyncio
import json
import sys


async def cmd_watch_orders(args: argparse.Namespace) -> None:
    import websockets
    from ave.config import TRADE_WSS_BASE, get_api_key
    url = f"{TRADE_WSS_BASE}?ave_access_key={get_api_key()}"
    async with websockets.connect(url) as ws:
        print("Connected. Subscribing to botswap...", file=sys.stderr)
        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": ["botswap"], "id": 0}))
        print("Subscribed. Waiting for botswap events...", file=sys.stderr)
        async for message in ws:
            try:
                print(json.dumps(json.loads(message), indent=2))
            except json.JSONDecodeError:
                print(message)
            print("---")


def main() -> None:
    from ave.config import IN_SERVER
    from ave.docker import docker_gate
    if not IN_SERVER:
        docker_gate("ave_trade_wss.py")

    parser = argparse.ArgumentParser(description="AVE Cloud Trade WebSocket client")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("watch-orders", help="Subscribe to proxy wallet order status push (botswap topic)")
    args = parser.parse_args()

    try:
        asyncio.run({"watch-orders": cmd_watch_orders}[args.command](args))
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
