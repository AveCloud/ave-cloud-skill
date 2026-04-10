"""Async WebSocket stream commands: watch-tx, watch-kline, watch-price."""

from __future__ import annotations

import argparse
import json

from ave.config import WSS_BASE, get_api_key
from ave.wss.formatter import KlineFormatter


def _ws_headers() -> dict[str, str]:
    return {"X-API-KEY": get_api_key()}


def _extract_kline_event(message: str) -> dict | None:
    try:
        body = json.loads(message)
    except json.JSONDecodeError:
        return None
    if not isinstance(body, dict):
        return None
    if body.get("type") == "kline":
        return body
    for key in ("params", "result", "data"):
        sub = body.get(key)
        if isinstance(sub, dict) and sub.get("type") == "kline":
            return sub
    result = body.get("result")
    if isinstance(result, dict) and result.get("topic") == "kline" and isinstance(result.get("kline"), dict):
        source = result["kline"].get("usd") or result["kline"].get("eth")
        if isinstance(source, dict):
            pair_id = result.get("id", "pair")
            chain, pair = "?", pair_id
            if isinstance(pair_id, str) and "-" in pair_id:
                pair, chain = pair_id.rsplit("-", 1)
            return {
                "type": "kline", "pair": pair, "chain": chain,
                "interval": result.get("interval"), "time": source.get("time"),
                "open": source.get("open"), "high": source.get("high"),
                "low": source.get("low"), "close": source.get("close"), "volume": source.get("volume"),
            }
    return None


async def cmd_watch_tx(args: argparse.Namespace) -> None:
    import websockets
    async with websockets.connect(WSS_BASE, additional_headers=_ws_headers()) as ws:
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": [args.topic, args.address, args.chain], "id": 1,
        }))
        print(f"Subscribed to {args.topic} for {args.address} on {args.chain}.", file=__import__("sys").stderr)
        async for message in ws:
            print(json.dumps(json.loads(message), indent=2), flush=True)
            print("---", flush=True)


async def cmd_watch_kline(args: argparse.Namespace) -> None:
    import websockets
    formatter = KlineFormatter(history=args.history) if args.format == "markdown" else None
    async with websockets.connect(WSS_BASE, additional_headers=_ws_headers()) as ws:
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": ["kline", args.address, args.interval, args.chain], "id": 1,
        }))
        print(f"Subscribed to kline for {args.address} on {args.chain} ({args.interval}).", file=__import__("sys").stderr)
        async for message in ws:
            if formatter:
                event = _extract_kline_event(message)
                if event:
                    print(formatter.render(event), flush=True)
                    print("---", flush=True)
                    continue
            print(json.dumps(json.loads(message), indent=2), flush=True)
            print("---", flush=True)


async def cmd_watch_price(args: argparse.Namespace) -> None:
    import websockets
    async with websockets.connect(WSS_BASE, additional_headers=_ws_headers()) as ws:
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": ["price", args.tokens], "id": 1,
        }))
        print(f"Subscribed to price for {len(args.tokens)} token(s).", file=__import__("sys").stderr)
        async for message in ws:
            print(json.dumps(json.loads(message), indent=2), flush=True)
            print("---", flush=True)
