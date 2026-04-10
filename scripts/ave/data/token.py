"""Token detail, price, and holder commands."""

import argparse

from ave.http import api_get, api_post
from ave.output import handle_response


async def cmd_token(args: argparse.Namespace) -> None:
    handle_response(await api_get(f"/tokens/{args.address}-{args.chain}"))


async def cmd_price(args: argparse.Namespace) -> None:
    evm_chains = ("-bsc", "-eth", "-base")
    payload: dict = {
        "token_ids": [t.lower() if t.endswith(evm_chains) else t for t in args.tokens],
    }
    if args.tvl_min:
        payload["tvl_min"] = int(args.tvl_min) if args.tvl_min.is_integer() else args.tvl_min
    if args.volume_min:
        payload["tx_24h_volume_min"] = int(args.volume_min) if args.volume_min.is_integer() else args.volume_min
    handle_response(await api_post("/tokens/price", payload))


async def cmd_holders(args: argparse.Namespace) -> None:
    params: dict = {}
    if args.limit:
        params["limit"] = args.limit
    if args.sort_by:
        params["sort_by"] = args.sort_by
    if args.order:
        params["order"] = args.order
    handle_response(await api_get(f"/tokens/holders/{args.address}-{args.chain}", params))
