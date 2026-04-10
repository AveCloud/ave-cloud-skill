"""Kline/OHLCV chart commands."""

import argparse
import json

from ave.http import api_get


def _trim_kline_points(body: dict, size: int) -> dict:
    points = body.get("data", {}).get("points")
    if isinstance(points, list) and len(points) > size:
        body["data"]["points"] = points[-size:]
        body["data"]["limit"] = size
        body["data"]["total_count"] = len(body["data"]["points"])
    return body


async def cmd_kline_token(args: argparse.Namespace) -> None:
    params = {"interval": args.interval, "limit": args.size}
    resp = await api_get(f"/klines/token/{args.address}-{args.chain}", params)
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    print(json.dumps(_trim_kline_points(resp.json(), args.size), indent=2))


async def cmd_kline_pair(args: argparse.Namespace) -> None:
    params = {"interval": args.interval, "limit": args.size}
    resp = await api_get(f"/klines/pair/{args.address}-{args.chain}", params)
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    print(json.dumps(_trim_kline_points(resp.json(), args.size), indent=2))


async def cmd_kline_ondo(args: argparse.Namespace) -> None:
    params: dict = {"interval": args.interval, "limit": args.size}
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.to_time is not None:
        params["to_time"] = args.to_time
    resp = await api_get(f"/klines/pair/ondo/{args.pair}", params)
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    body = resp.json()
    data = body.get("data")
    if isinstance(data, dict):
        points = data.get("points")
        if isinstance(points, list) and len(points) > args.size:
            data["points"] = points[-args.size:]
            data["limit"] = args.size
            data["total_count"] = len(data["points"])
    elif isinstance(data, list) and len(data) > args.size:
        body["data"] = data[-args.size:]
    print(json.dumps(body, indent=2))
