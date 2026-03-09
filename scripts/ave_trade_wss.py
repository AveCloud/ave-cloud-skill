#!/usr/bin/env python3
"""AVE Cloud Trade WebSocket client CLI.

Usage: python ave_trade_wss.py <command> [options]
Requires: AVE_API_KEY environment variable
"""

import argparse
import json
import sys

from ave_trade_rest import IN_SERVER, _docker_gate, get_api_key

TRADE_WSS_BASE = "wss://bot-api.ave.ai/thirdws"


def cmd_watch_orders(args):
    try:
        import websocket
    except ImportError:
        raise ImportError(
            "websocket-client is required. Run: pip install websocket-client>=1.6.0"
        )

    api_key = get_api_key()
    url = f"{TRADE_WSS_BASE}?ave_access_key={api_key}"
    subscribe_msg = json.dumps({
        "jsonrpc": "2.0",
        "method": "subscribe",
        "params": ["botswap"],
        "id": 0,
    })

    def on_open(ws):
        print("Connected. Subscribing to botswap...", file=sys.stderr)
        ws.send(subscribe_msg)
        print("Subscribed. Waiting for botswap events...", file=sys.stderr)

    def on_message(ws, message):
        try:
            print(json.dumps(json.loads(message), indent=2))
        except json.JSONDecodeError:
            print(message)
        print("---")

    def on_error(ws, error):
        print(f"WebSocket error: {error}", file=sys.stderr)

    def on_close(ws, close_status_code, close_msg):
        print("Connection closed.", file=sys.stderr)

    print(f"Connecting to {TRADE_WSS_BASE}...", file=sys.stderr)
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(ping_interval=30, ping_timeout=10)


def main():
    if not IN_SERVER:
        _docker_gate("ave_trade_wss.py")

    parser = argparse.ArgumentParser(description="AVE Cloud Trade WebSocket client")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "watch-orders",
        help="Subscribe to proxy wallet order status push (botswap topic)",
    )

    args = parser.parse_args()

    commands = {"watch-orders": cmd_watch_orders}

    try:
        commands[args.command](args)
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
