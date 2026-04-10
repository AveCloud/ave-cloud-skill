"""Proxy wallet commands: wallet management, orders, approvals, transfers."""

import argparse
import json

from ave.http import trade_get, trade_post
from ave.output import handle_response


async def cmd_list_wallets(args: argparse.Namespace) -> None:
    params: dict = {}
    if args.assets_ids:
        params["assetsIds"] = args.assets_ids
    handle_response(await trade_get("/v1/thirdParty/user/getUserByAssetsId", params or None, proxy=True))


async def cmd_create_wallet(args: argparse.Namespace) -> None:
    payload: dict = {"assetsName": args.name}
    if args.return_mnemonic:
        payload["returnMnemonic"] = True
    handle_response(await trade_post("/v1/thirdParty/user/generateWallet", payload, proxy=True))


async def cmd_delete_wallet(args: argparse.Namespace) -> None:
    handle_response(await trade_post("/v1/thirdParty/user/deleteWallet", {"assetsIds": args.assets_ids}, proxy=True))


async def cmd_market_order(args: argparse.Namespace) -> None:
    payload: dict = {
        "chain": args.chain, "assetsId": args.assets_id, "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token, "inAmount": args.in_amount,
        "swapType": args.swap_type, "slippage": args.slippage, "useMev": args.use_mev,
    }
    if args.gas:
        payload["gas"] = args.gas
    if args.extra_gas:
        payload["extraGas"] = args.extra_gas
    if args.auto_slippage:
        payload["autoSlippage"] = True
    if args.auto_gas:
        payload["autoGas"] = args.auto_gas
    if args.auto_sell:
        payload["autoSellConfig"] = [json.loads(r) for r in args.auto_sell]
    handle_response(await trade_post("/v1/thirdParty/tx/sendSwapOrder", payload, proxy=True))


async def cmd_limit_order(args: argparse.Namespace) -> None:
    payload: dict = {
        "chain": args.chain, "assetsId": args.assets_id, "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token, "inAmount": args.in_amount,
        "swapType": args.swap_type, "slippage": args.slippage, "useMev": args.use_mev,
        "limitPrice": args.limit_price,
    }
    if args.gas:
        payload["gas"] = args.gas
    if args.extra_gas:
        payload["extraGas"] = args.extra_gas
    if args.expire_time:
        payload["expireTime"] = args.expire_time
    if args.auto_slippage:
        payload["autoSlippage"] = True
    if args.auto_gas:
        payload["autoGas"] = args.auto_gas
    handle_response(await trade_post("/v1/thirdParty/tx/sendLimitOrder", payload, proxy=True))


async def cmd_get_swap_orders(args: argparse.Namespace) -> None:
    handle_response(await trade_get("/v1/thirdParty/tx/getSwapOrder", {"chain": args.chain, "ids": args.ids}, proxy=True))


async def cmd_get_limit_orders(args: argparse.Namespace) -> None:
    params: dict = {"chain": args.chain, "assetsId": args.assets_id, "pageSize": args.page_size, "pageNo": args.page_no}
    if args.status:
        params["status"] = args.status
    if args.token:
        params["token"] = args.token
    handle_response(await trade_get("/v1/thirdParty/tx/getLimitOrder", params, proxy=True))


async def cmd_cancel_limit_order(args: argparse.Namespace) -> None:
    handle_response(await trade_post("/v1/thirdParty/tx/cancelLimitOrder", {"chain": args.chain, "ids": args.ids}, proxy=True))


async def cmd_approve_token(args: argparse.Namespace) -> None:
    payload = {"chain": args.chain, "assetsId": args.assets_id, "tokenAddress": args.token_address}
    handle_response(await trade_post("/v1/thirdParty/tx/approve", payload, proxy=True))


async def cmd_get_approval(args: argparse.Namespace) -> None:
    handle_response(await trade_get("/v1/thirdParty/tx/getApprove", {"chain": args.chain, "ids": args.ids}, proxy=True))


async def cmd_transfer(args: argparse.Namespace) -> None:
    payload: dict = {
        "chain": args.chain, "assetsId": args.assets_id, "fromAddress": args.from_address,
        "toAddress": args.to_address, "tokenAddress": args.token_address, "amount": args.amount,
    }
    if args.gas:
        payload["gas"] = args.gas
    if args.extra_gas:
        payload["extraGas"] = args.extra_gas
    handle_response(await trade_post("/v1/thirdParty/tx/transfer", payload, proxy=True))


async def cmd_get_transfer(args: argparse.Namespace) -> None:
    handle_response(await trade_get("/v1/thirdParty/tx/getTransfer", {"chain": args.chain, "ids": args.ids}, proxy=True))
