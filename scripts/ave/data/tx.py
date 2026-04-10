"""Transaction, pair, and signal commands."""

import argparse

from ave.http import api_get
from ave.output import handle_response


async def cmd_txs(args: argparse.Namespace) -> None:
    handle_response(await api_get(f"/txs/{args.address}-{args.chain}"))


async def cmd_liq_txs(args: argparse.Namespace) -> None:
    params: dict = {"limit": args.limit, "sort": args.sort}
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.to_time is not None:
        params["to_time"] = args.to_time
    if args.type:
        params["type"] = args.type
    handle_response(await api_get(f"/txs/liq/{args.address}-{args.chain}", params))


async def cmd_tx_detail(args: argparse.Namespace) -> None:
    params: dict = {"chain": args.chain, "account_address": args.account, "tx_hash": args.tx_hash}
    if args.start_from is not None:
        params["start_from"] = args.start_from
    if args.end_at is not None:
        params["end_at"] = args.end_at
    if args.limit:
        params["limit"] = args.limit
    handle_response(await api_get("/txs/detail", params))


async def cmd_pair(args: argparse.Namespace) -> None:
    handle_response(await api_get(f"/pairs/{args.address}-{args.chain}"))


async def cmd_signals(args: argparse.Namespace) -> None:
    params = {"chain": args.chain, "pageSize": args.page_size, "pageNO": args.page_no}
    handle_response(await api_get("/signals/public/list", params))
