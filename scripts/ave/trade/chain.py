"""Chain wallet commands: quote, create/send/swap for EVM and Solana."""

import argparse
import json
import os

from ave.config import CHAIN_ID, RPC_ENV
from ave.http import rpc_call, trade_post
from ave.output import handle_response, response_ok
from ave.trade.signing import checksum_address, get_evm_account, get_solana_keypair, sign_evm_tx, sign_solana_tx


def _validate_fee_recipient_args(args: argparse.Namespace) -> None:
    has_recipient = bool(getattr(args, "fee_recipient", None))
    has_rate = bool(getattr(args, "fee_recipient_rate", None))
    if has_recipient != has_rate:
        raise ValueError("feeRecipient and feeRecipientRate must be provided together.")


async def cmd_quote(args: argparse.Namespace) -> None:
    payload = {
        "chain": args.chain, "inAmount": args.in_amount,
        "inTokenAddress": args.in_token, "outTokenAddress": args.out_token, "swapType": args.swap_type,
    }
    handle_response(await trade_post("/v1/thirdParty/chainWallet/getAmountOut", payload))


async def cmd_approve_chain(args: argparse.Namespace) -> None:
    account = get_evm_account()
    rpc_url = args.rpc_url or os.environ.get(RPC_ENV[args.chain])
    if not rpc_url:
        raise EnvironmentError(f"approve-chain requires RPC. Pass --rpc-url or set {RPC_ENV[args.chain]}.")
    # Get spender from quote
    quote_resp = await trade_post("/v1/thirdParty/chainWallet/getAmountOut", {
        "chain": args.chain, "inAmount": args.in_amount or "1000000000000000000",
        "inTokenAddress": args.token, "outTokenAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "swapType": "sell",
    })
    quote_json = quote_resp.json()
    if quote_resp.status_code >= 400 or not response_ok(quote_json):
        raise RuntimeError(f"quote failed: {quote_resp.text}")
    spender = quote_json["data"]["spender"]
    # ERC-20 approve(spender, MAX_UINT256)
    max_uint = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    calldata = "0x095ea7b3" + spender[2:].lower().zfill(64) + max_uint
    nonce = int(await rpc_call(rpc_url, "eth_getTransactionCount", [account.address, "latest"]), 16)
    gas_price = int(await rpc_call(rpc_url, "eth_gasPrice", []), 16)
    tx_dict = {
        "to": checksum_address(args.token), "data": calldata, "gas": 60000,
        "value": 0, "nonce": nonce, "gasPrice": gas_price, "chainId": CHAIN_ID[args.chain],
    }
    signed_tx = sign_evm_tx(tx_dict, account.key)
    tx_hash = await rpc_call(rpc_url, "eth_sendRawTransaction", [signed_tx])
    print(json.dumps({"status": "approved", "spender": spender, "token": args.token, "chain": args.chain, "txHash": tx_hash}, indent=2))


async def cmd_create_evm_tx(args: argparse.Namespace) -> None:
    _validate_fee_recipient_args(args)
    payload: dict = {
        "chain": args.chain, "creatorAddress": args.creator_address,
        "inAmount": args.in_amount, "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token, "swapType": args.swap_type, "slippage": args.slippage,
    }
    if args.fee_recipient:
        payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        payload["autoSlippage"] = True
    handle_response(await trade_post("/v1/thirdParty/chainWallet/createEvmTx", payload))


async def cmd_send_evm_tx(args: argparse.Namespace) -> None:
    payload: dict = {"chain": args.chain, "requestTxId": args.request_tx_id, "signedTx": args.signed_tx}
    if args.use_mev:
        payload["useMev"] = True
    handle_response(await trade_post("/v1/thirdParty/chainWallet/sendSignedEvmTx", payload))


async def cmd_create_solana_tx(args: argparse.Namespace) -> None:
    _validate_fee_recipient_args(args)
    payload: dict = {
        "creatorAddress": args.creator_address, "inAmount": args.in_amount,
        "inTokenAddress": args.in_token, "outTokenAddress": args.out_token,
        "swapType": args.swap_type, "slippage": args.slippage, "fee": args.fee,
    }
    if args.use_mev:
        payload["useMev"] = True
    if args.fee_recipient:
        payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        payload["autoSlippage"] = True
    handle_response(await trade_post("/v1/thirdParty/chainWallet/createSolanaTx", payload))


async def cmd_send_solana_tx(args: argparse.Namespace) -> None:
    payload: dict = {"requestTxId": args.request_tx_id, "signedTx": args.signed_tx}
    if args.use_mev:
        payload["useMev"] = True
    handle_response(await trade_post("/v1/thirdParty/chainWallet/sendSignedSolanaTx", payload))


async def cmd_swap_evm(args: argparse.Namespace) -> None:
    _validate_fee_recipient_args(args)
    account = get_evm_account()
    rpc_url = args.rpc_url or os.environ.get(RPC_ENV[args.chain])
    if not rpc_url:
        raise EnvironmentError(f"swap-evm requires RPC. Pass --rpc-url or set {RPC_ENV[args.chain]}.")
    create_payload: dict = {
        "chain": args.chain, "creatorAddress": account.address,
        "inAmount": args.in_amount, "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token, "swapType": args.swap_type, "slippage": args.slippage,
    }
    if args.fee_recipient:
        create_payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        create_payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        create_payload["autoSlippage"] = True
    resp = await trade_post("/v1/thirdParty/chainWallet/createEvmTx", create_payload)
    resp_json = resp.json()
    if resp.status_code >= 400 or not response_ok(resp_json):
        raise RuntimeError(f"create-evm-tx failed: {resp.text}")
    create_data = resp_json["data"]
    tx_content = create_data["txContent"]
    tx_data = tx_content["data"]
    if not tx_data.startswith("0x"):
        tx_data = "0x" + tx_data
    nonce = int(await rpc_call(rpc_url, "eth_getTransactionCount", [account.address, "latest"]), 16)
    gas_price = int(await rpc_call(rpc_url, "eth_gasPrice", []), 16)
    gas_limit = int(create_data["gasLimit"])
    if gas_limit == 0:
        est = await rpc_call(rpc_url, "eth_estimateGas", [{
            "from": account.address, "to": tx_content["to"],
            "data": tx_data, "value": hex(int(tx_content.get("value", "0"))),
        }])
        gas_limit = int(int(est, 16) * 1.3)
    tx_dict = {
        "to": tx_content["to"], "data": tx_data, "gas": gas_limit,
        "value": int(tx_content.get("value", "0")), "nonce": nonce,
        "gasPrice": gas_price, "chainId": CHAIN_ID[args.chain],
    }
    signed_tx = sign_evm_tx(tx_dict, account.key)
    send_payload: dict = {"chain": args.chain, "requestTxId": create_data["requestTxId"], "signedTx": signed_tx}
    if args.use_mev:
        send_payload["useMev"] = True
    handle_response(await trade_post("/v1/thirdParty/chainWallet/sendSignedEvmTx", send_payload))


async def cmd_swap_solana(args: argparse.Namespace) -> None:
    _validate_fee_recipient_args(args)
    keypair = get_solana_keypair()
    create_payload: dict = {
        "creatorAddress": str(keypair.pubkey()), "inAmount": args.in_amount,
        "inTokenAddress": args.in_token, "outTokenAddress": args.out_token,
        "swapType": args.swap_type, "slippage": args.slippage, "fee": args.fee,
    }
    if args.use_mev:
        create_payload["useMev"] = True
    if args.fee_recipient:
        create_payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        create_payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        create_payload["autoSlippage"] = True
    resp = await trade_post("/v1/thirdParty/chainWallet/createSolanaTx", create_payload)
    resp_json = resp.json()
    if resp.status_code >= 400 or not response_ok(resp_json):
        raise RuntimeError(f"create-solana-tx failed: {resp.text}")
    create_data = resp_json["data"]
    tx_content = create_data.get("txContent") or create_data.get("txContext")
    if not tx_content:
        raise RuntimeError(f"create-solana-tx missing txContent/txContext: {resp.text}")
    signed_tx = sign_solana_tx(tx_content, keypair)
    send_payload: dict = {"requestTxId": create_data["requestTxId"], "signedTx": signed_tx}
    if args.use_mev:
        send_payload["useMev"] = True
    handle_response(await trade_post("/v1/thirdParty/chainWallet/sendSignedSolanaTx", send_payload))
