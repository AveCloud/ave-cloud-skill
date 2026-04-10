"""Wallet and address commands."""

import argparse

from ave.http import api_get
from ave.output import handle_response


async def cmd_address_txs(args: argparse.Namespace) -> None:
    params: dict = {"wallet_address": args.wallet, "chain": args.chain}
    if args.token:
        params["token_address"] = args.token
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.last_time:
        params["last_time"] = args.last_time
    if args.last_id:
        params["last_id"] = args.last_id
    if args.page_size:
        params["page_size"] = args.page_size
    handle_response(await api_get("/address/tx", params))


async def cmd_address_pnl(args: argparse.Namespace) -> None:
    params = {"wallet_address": args.wallet, "chain": args.chain, "token_address": args.token}
    handle_response(await api_get("/address/pnl", params))


async def cmd_wallet_tokens(args: argparse.Namespace) -> None:
    params: dict = {"wallet_address": args.wallet, "chain": args.chain}
    if args.sort:
        params["sort"] = args.sort
    if args.sort_dir:
        params["sort_dir"] = args.sort_dir
    if args.page_size:
        params["pageSize"] = args.page_size
    if args.page_no:
        params["pageNO"] = args.page_no
    if args.hide_sold:
        params["hide_sold"] = 1
    if args.hide_small is not None:
        params["hide_small"] = args.hide_small
    if args.blue_chips:
        params["blue_chips"] = 1
    handle_response(await api_get("/address/walletinfo/tokens", params))


async def cmd_wallet_info(args: argparse.Namespace) -> None:
    params: dict = {"wallet_address": args.wallet, "chain": args.chain}
    if args.self_address:
        params["self_address"] = args.self_address
    handle_response(await api_get("/address/walletinfo", params))


async def cmd_smart_wallets(args: argparse.Namespace) -> None:
    params: dict = {"chain": args.chain}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.sort:
        params["sort"] = args.sort
    if args.sort_dir:
        params["sort_dir"] = args.sort_dir
    for name in (
        "profit_above_900_percent_num_min", "profit_above_900_percent_num_max",
        "profit_300_900_percent_num_min", "profit_300_900_percent_num_max",
        "profit_100_300_percent_num_min", "profit_100_300_percent_num_max",
        "profit_10_100_percent_num_min", "profit_10_100_percent_num_max",
        "profit_neg10_10_percent_num_min", "profit_neg10_10_percent_num_max",
        "profit_neg50_neg10_percent_num_min", "profit_neg50_neg10_percent_num_max",
        "profit_neg100_neg50_percent_num_min", "profit_neg100_neg50_percent_num_max",
        "last_trade_time_min", "last_trade_time_max",
    ):
        val = getattr(args, name, None)
        if val is not None:
            params[name] = val
    handle_response(await api_get("/address/smart_wallet/list", params))
