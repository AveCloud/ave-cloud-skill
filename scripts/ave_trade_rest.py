#!/usr/bin/env python3
"""AVE Cloud Trade REST API client CLI.

Usage: python ave_trade_rest.py <command> [options]
Requires: AVE_API_KEY environment variable
"""

import argparse
import base64
import datetime
import fcntl
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TRADE_BASE = "https://bot-api.ave.ai"
TRADE_RATE_LIMIT_FILE = "/tmp/ave_trade_last_request"

VALID_PLANS = ("free", "normal", "pro")
PLAN_RPS = {"free": 1, "normal": 5, "pro": 20}
PLAN_MIN_INTERVAL = {"free": 1.0, "normal": 0.2, "pro": 0.05}

EVM_CHAINS = ("bsc", "eth", "base")
ALL_CHAINS = ("bsc", "eth", "base", "solana")
NATIVE_COIN = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
CHAIN_ID = {"bsc": 56, "eth": 1, "base": 8453}
RPC_ENV = {
    "bsc": "AVE_BSC_RPC_URL",
    "eth": "AVE_ETH_RPC_URL",
    "base": "AVE_BASE_RPC_URL",
}

USE_DOCKER = os.environ.get("AVE_USE_DOCKER", "").lower() in ("1", "true", "yes")
IN_SERVER = os.environ.get("AVE_IN_SERVER", "").lower() in ("1", "true", "yes")

_DOCKER_MODE_FILE = os.path.expanduser("~/.ave_cloud_docker_mode")


def _ask_docker_mode():
    """Prompt user for docker vs host mode. Saves choice. Returns True for Docker."""
    if os.path.exists(_DOCKER_MODE_FILE):
        try:
            saved = open(_DOCKER_MODE_FILE).read().strip()
            if saved in ("true", "false"):
                return saved == "true"
        except OSError:
            pass
    if not sys.stdin.isatty():
        return True
    sys.stderr.write(
        "\nAVE_USE_DOCKER is not set. Choose execution mode:\n"
        "  [1] Docker (recommended) — run inside Docker container\n"
        "  [2] Host — install requirements.txt and run directly\n"
        "Choice [1]: "
    )
    sys.stderr.flush()
    try:
        answer = sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    use_docker = answer != "2"
    try:
        with open(_DOCKER_MODE_FILE, "w") as f:
            f.write("true" if use_docker else "false")
        print(
            f"Saved. To reset: rm {_DOCKER_MODE_FILE}  or set AVE_USE_DOCKER=true/false.",
            file=sys.stderr,
        )
    except OSError:
        pass
    return use_docker


def _ensure_docker_image():
    r = subprocess.run(["docker", "image", "inspect", "ave-cloud"], capture_output=True)
    if r.returncode != 0:
        print("Building Docker image 'ave-cloud'...", file=sys.stderr)
        r2 = subprocess.run(
            ["docker", "build", "-f", "scripts/Dockerfile.txt", "-t", "ave-cloud", "."]
        )
        if r2.returncode != 0:
            print("Error: Docker build failed.", file=sys.stderr)
            sys.exit(1)


def _reexec_in_docker(script_name):
    """Re-run this command inside a one-shot Docker container and exit."""
    _ensure_docker_image()
    env_args = []
    for var in (
        "AVE_API_KEY", "API_PLAN", "AVE_SECRET_KEY",
        "AVE_EVM_PRIVATE_KEY", "AVE_SOLANA_PRIVATE_KEY", "AVE_MNEMONIC",
        "AVE_BSC_RPC_URL", "AVE_ETH_RPC_URL", "AVE_BASE_RPC_URL",
    ):
        val = os.environ.get(var)
        if val:
            env_args += ["-e", f"{var}={val}"]
    result = subprocess.run([
        "docker", "run", "--rm",
        "--entrypoint", "python",
        "-e", "AVE_USE_DOCKER=true",
        "-e", "AVE_IN_SERVER=true",
        *env_args,
        "ave-cloud", f"scripts/{script_name}",
        *sys.argv[1:],
    ])
    sys.exit(result.returncode)


def _ensure_requirements():
    """Pip-install requirements.txt if requests is not available."""
    try:
        import requests  # noqa: F401
    except ImportError:
        req = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        print(f"Installing {req}...", file=sys.stderr)
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", req])
        if r.returncode != 0:
            print("Error: pip install failed.", file=sys.stderr)
            sys.exit(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)


def _docker_gate(script_name):
    """Determine exec mode from AVE_USE_DOCKER (or prompt). Must be called before work starts."""
    env_val = os.environ.get("AVE_USE_DOCKER", "").lower()
    if env_val in ("1", "true", "yes"):
        _reexec_in_docker(script_name)
    elif env_val in ("0", "false", "no"):
        _ensure_requirements()
    else:
        if _ask_docker_mode():
            _reexec_in_docker(script_name)
        else:
            _ensure_requirements()


def get_api_key():
    key = os.environ.get("AVE_API_KEY")
    if not key:
        raise EnvironmentError(
            "AVE_API_KEY environment variable not set. "
            "Get a key at https://cloud.ave.ai/register"
        )
    return key


def get_api_plan():
    plan = os.environ.get("API_PLAN", "free")
    if plan not in VALID_PLANS:
        raise ValueError(f"API_PLAN must be one of: {', '.join(VALID_PLANS)}")
    return plan


def _get_secret_key():
    key = os.environ.get("AVE_SECRET_KEY")
    if not key:
        raise EnvironmentError(
            "AVE_SECRET_KEY environment variable not set. Required for proxy wallet operations."
        )
    return key


def _make_session():
    try:
        import warnings
        warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
        from requests_ratelimiter import LimiterSession
    except ImportError:
        raise ImportError(
            "requests or requests-ratelimiter is not installed. "
            "Run: pip install -r scripts/requirements.txt"
        )
    rps = PLAN_RPS[get_api_plan()]
    return LimiterSession(per_second=rps)


_session = None


def _get_session():
    global _session
    if _session is None:
        _session = _make_session()
    return _session


def _builtin_rate_limit():
    min_interval = PLAN_MIN_INTERVAL[get_api_plan()]
    with open(TRADE_RATE_LIMIT_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        content = f.read().strip()
        last = float(content) if content else 0.0
        wait = min_interval - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        f.seek(0)
        f.truncate()
        f.write(str(time.time()))


def _trade_sign(method: str, path: str, body=None):
    secret = _get_secret_key()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    message = timestamp + method.upper().strip() + path.strip()
    if body:
        if isinstance(body, dict):
            message += json.dumps(body, sort_keys=True, separators=(",", ":"))
        else:
            message += str(body).strip()
    h = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
    return timestamp, base64.b64encode(h.digest()).decode()


def _chain_headers():
    return {"AVE-ACCESS-KEY": get_api_key(), "Content-Type": "application/json"}


def _proxy_headers(method: str, path: str, body=None):
    timestamp, signature = _trade_sign(method, path, body)
    return {
        "AVE-ACCESS-KEY": get_api_key(),
        "AVE-ACCESS-TIMESTAMP": timestamp,
        "AVE-ACCESS-SIGN": signature,
        "Content-Type": "application/json",
    }


class _Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    @property
    def text(self):
        return self._body

    def json(self):
        return json.loads(self._body)


def _urllib_get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return _Response(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return _Response(e.code, body)


def _urllib_post(url, payload, headers):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return _Response(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return _Response(e.code, body)


def trade_get(path, params=None, proxy=False):
    url = f"{TRADE_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = _proxy_headers("GET", path) if proxy else _chain_headers()
    if USE_DOCKER:
        return _get_session().get(url, headers=headers)
    _builtin_rate_limit()
    return _urllib_get(url, headers)


def trade_post(path, payload, proxy=False):
    url = f"{TRADE_BASE}{path}"
    headers = _proxy_headers("POST", path, payload) if proxy else _chain_headers()
    if USE_DOCKER:
        return _get_session().post(url, headers=headers, json=payload)
    _builtin_rate_limit()
    return _urllib_post(url, payload, headers)


def handle_response(resp):
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    body = resp.json()
    if isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, dict) and "txContext" in data and "txContent" not in data:
            # PROD currently returns `txContext` for Solana create tx responses.
            data["txContent"] = data["txContext"]
        status = body.get("status")
        if status is not None and status not in (0, 1, 200):
            msg = body.get("msg", "")
            raise RuntimeError(f"API status {status}: {msg}".strip())
    print(json.dumps(body, indent=2))


def _rpc_call(rpc_url, method, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        rpc_url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        if "error" in body:
            raise RuntimeError(f"RPC error: {body['error']}")
        return body["result"]


def _mnemonic_to_seed(mnemonic: str) -> bytes:
    import unicodedata
    mnemonic_b = unicodedata.normalize("NFKD", mnemonic).encode("utf-8")
    salt = b"mnemonic"
    return hashlib.pbkdf2_hmac("sha512", mnemonic_b, salt, 2048)


def _slip010_derive(seed: bytes, path: str) -> bytes:
    I = hmac.new(b"ed25519 seed", seed, hashlib.sha512).digest()
    key, chain_code = I[:32], I[32:]
    for comp in path.split("/")[1:]:
        hardened = comp.endswith("'")
        index = int(comp.rstrip("'"))
        if hardened:
            index += 0x80000000
        data = b"\x00" + key + index.to_bytes(4, "big")
        I = hmac.new(chain_code, data, hashlib.sha512).digest()
        key, chain_code = I[:32], I[32:]
    return key


def _get_evm_account():
    try:
        from eth_account import Account
    except ImportError:
        raise ImportError("eth-account is required. Run: pip install eth-account>=0.10.0")

    raw_key = os.environ.get("AVE_EVM_PRIVATE_KEY")
    if raw_key:
        return Account.from_key(raw_key)

    mnemonic = os.environ.get("AVE_MNEMONIC")
    if not mnemonic:
        raise EnvironmentError(
            "EVM signing requires AVE_EVM_PRIVATE_KEY or AVE_MNEMONIC to be set."
        )
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")


def _get_solana_keypair():
    try:
        from solders.keypair import Keypair
    except ImportError:
        raise ImportError("solders is required. Run: pip install solders>=0.20.0")

    raw_key = os.environ.get("AVE_SOLANA_PRIVATE_KEY")
    if raw_key:
        return Keypair.from_base58_string(raw_key)

    mnemonic = os.environ.get("AVE_MNEMONIC")
    if not mnemonic:
        raise EnvironmentError(
            "Solana signing requires AVE_SOLANA_PRIVATE_KEY or AVE_MNEMONIC to be set."
        )
    seed = _mnemonic_to_seed(mnemonic)
    key_bytes = _slip010_derive(seed, "m/44'/501'/0'/0'")
    return Keypair.from_seed(key_bytes)


def _sign_evm_tx(tx_dict: dict, private_key) -> str:
    try:
        from eth_account import Account
    except ImportError:
        raise ImportError("eth-account is required. Run: pip install eth-account>=0.10.0")
    signed = Account.sign_transaction(tx_dict, private_key)
    return "0x" + signed.raw_transaction.hex()


def _get_required_evm_rpc_url(chain: str, cli_rpc_url) -> str:
    rpc_url = cli_rpc_url or os.environ.get(RPC_ENV[chain])
    if rpc_url:
        return rpc_url
    raise EnvironmentError(
        f"swap-evm requires a user-provided RPC node for {chain}. "
        f"Pass --rpc-url or set {RPC_ENV[chain]}."
    )


def _sign_solana_tx(tx_content_b64: str, keypair) -> str:
    try:
        from solders.message import MessageV0
        from solders.transaction import VersionedTransaction
    except ImportError:
        raise ImportError("solders is required. Run: pip install solders>=0.20.0")
    tx_bytes = base64.b64decode(tx_content_b64)
    # txContent includes a 0x80 version prefix byte before the MessageV0 body
    msg = MessageV0.from_bytes(tx_bytes[1:])
    signed = VersionedTransaction(msg, [keypair])
    return base64.b64encode(bytes(signed)).decode()


# --- Chain wallet commands ---

def cmd_quote(args):
    payload = {
        "chain": args.chain,
        "inAmount": args.in_amount,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "swapType": args.swap_type,
    }
    handle_response(trade_post("/v1/thirdParty/chainWallet/getAmountOut", payload))


def cmd_create_evm_tx(args):
    payload = {
        "chain": args.chain,
        "creatorAddress": args.creator_address,
        "inAmount": args.in_amount,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "swapType": args.swap_type,
        "slippage": args.slippage,
    }
    if args.fee_recipient:
        payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        payload["autoSlippage"] = True
    handle_response(trade_post("/v1/thirdParty/chainWallet/createEvmTx", payload))


def cmd_send_evm_tx(args):
    payload = {
        "chain": args.chain,
        "requestTxId": args.request_tx_id,
        "signedTx": args.signed_tx,
    }
    if args.use_mev:
        payload["useMev"] = True
    handle_response(trade_post("/v1/thirdParty/chainWallet/sendSignedEvmTx", payload))


def cmd_create_solana_tx(args):
    payload = {
        "creatorAddress": args.creator_address,
        "inAmount": args.in_amount,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "swapType": args.swap_type,
        "slippage": args.slippage,
        "fee": args.fee,
    }
    if args.use_mev:
        payload["useMev"] = True
    if args.fee_recipient:
        payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        payload["autoSlippage"] = True
    handle_response(trade_post("/v1/thirdParty/chainWallet/createSolanaTx", payload))


def cmd_send_solana_tx(args):
    payload = {
        "requestTxId": args.request_tx_id,
        "signedTx": args.signed_tx,
    }
    if args.use_mev:
        payload["useMev"] = True
    handle_response(trade_post("/v1/thirdParty/chainWallet/sendSignedSolanaTx", payload))


def cmd_swap_evm(args):
    account = _get_evm_account()
    creator_address = account.address
    rpc_url = _get_required_evm_rpc_url(args.chain, args.rpc_url)

    create_payload = {
        "chain": args.chain,
        "creatorAddress": creator_address,
        "inAmount": args.in_amount,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "swapType": args.swap_type,
        "slippage": args.slippage,
    }
    if args.fee_recipient:
        create_payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        create_payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        create_payload["autoSlippage"] = True

    resp = trade_post("/v1/thirdParty/chainWallet/createEvmTx", create_payload)
    resp_json = resp.json()
    if resp.status_code >= 400 or resp_json.get("status") != 200:
        raise RuntimeError(f"create-evm-tx failed: {resp.text}")
    create_data = resp_json["data"]

    tx_content = create_data["txContent"]
    tx_data = tx_content["data"]
    if not tx_data.startswith("0x"):
        tx_data = "0x" + tx_data
    nonce = int(_rpc_call(rpc_url, "eth_getTransactionCount", [creator_address, "latest"]), 16)
    gas_price = int(_rpc_call(rpc_url, "eth_gasPrice", []), 16)

    gas_limit = int(create_data["gasLimit"])
    if gas_limit == 0:
        est = _rpc_call(rpc_url, "eth_estimateGas", [{
            "from": creator_address,
            "to": tx_content["to"],
            "data": tx_data,
            "value": hex(int(tx_content.get("value", "0"))),
        }])
        gas_limit = int(int(est, 16) * 1.3)

    tx_dict = {
        "to": tx_content["to"],
        "data": tx_data,
        "gas": gas_limit,
        "value": int(tx_content.get("value", "0")),
        "nonce": nonce,
        "gasPrice": gas_price,
        "chainId": CHAIN_ID[args.chain],
    }
    signed_tx = _sign_evm_tx(tx_dict, account.key)

    send_payload = {
        "chain": args.chain,
        "requestTxId": create_data["requestTxId"],
        "signedTx": signed_tx,
    }
    if args.use_mev:
        send_payload["useMev"] = True
    handle_response(trade_post("/v1/thirdParty/chainWallet/sendSignedEvmTx", send_payload))


def cmd_swap_solana(args):
    keypair = _get_solana_keypair()
    creator_address = str(keypair.pubkey())

    create_payload = {
        "creatorAddress": creator_address,
        "inAmount": args.in_amount,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "swapType": args.swap_type,
        "slippage": args.slippage,
        "fee": args.fee,
    }
    if args.use_mev:
        create_payload["useMev"] = True
    if args.fee_recipient:
        create_payload["feeRecipient"] = args.fee_recipient
    if args.fee_recipient_rate:
        create_payload["feeRecipientRate"] = args.fee_recipient_rate
    if args.auto_slippage:
        create_payload["autoSlippage"] = True

    resp = trade_post("/v1/thirdParty/chainWallet/createSolanaTx", create_payload)
    resp_json = resp.json()
    if resp.status_code >= 400 or resp_json.get("status") != 200:
        raise RuntimeError(f"create-solana-tx failed: {resp.text}")
    create_data = resp_json["data"]
    tx_content = create_data.get("txContent") or create_data.get("txContext")
    if not tx_content:
        raise RuntimeError(f"create-solana-tx missing txContent/txContext: {resp.text}")
    signed_tx = _sign_solana_tx(tx_content, keypair)

    send_payload = {"requestTxId": create_data["requestTxId"], "signedTx": signed_tx}
    if args.use_mev:
        send_payload["useMev"] = True
    handle_response(trade_post("/v1/thirdParty/chainWallet/sendSignedSolanaTx", send_payload))


# --- Proxy wallet commands ---

def cmd_list_wallets(args):
    params = {}
    if args.assets_ids:
        params["assetsIds"] = args.assets_ids
    handle_response(trade_get("/v1/thirdParty/user/getUserByAssetsId", params or None, proxy=True))


def cmd_create_wallet(args):
    payload = {"assetsName": args.name}
    if args.return_mnemonic:
        payload["returnMnemonic"] = True
    handle_response(trade_post("/v1/thirdParty/user/generateWallet", payload, proxy=True))


def cmd_delete_wallet(args):
    payload = {"assetsIds": args.assets_ids}
    handle_response(trade_post("/v1/thirdParty/user/deleteWallet", payload, proxy=True))


def cmd_market_order(args):
    payload = {
        "chain": args.chain,
        "assetsId": args.assets_id,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "inAmount": args.in_amount,
        "swapType": args.swap_type,
        "slippage": args.slippage,
        "useMev": args.use_mev,
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
    handle_response(trade_post("/v1/thirdParty/tx/sendSwapOrder", payload, proxy=True))


def cmd_limit_order(args):
    payload = {
        "chain": args.chain,
        "assetsId": args.assets_id,
        "inTokenAddress": args.in_token,
        "outTokenAddress": args.out_token,
        "inAmount": args.in_amount,
        "swapType": args.swap_type,
        "slippage": args.slippage,
        "useMev": args.use_mev,
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
    handle_response(trade_post("/v1/thirdParty/tx/sendLimitOrder", payload, proxy=True))


def cmd_get_swap_orders(args):
    handle_response(trade_get(
        "/v1/thirdParty/tx/getSwapOrder", {"chain": args.chain, "ids": args.ids}, proxy=True
    ))


def cmd_get_limit_orders(args):
    params = {
        "chain": args.chain,
        "assetsId": args.assets_id,
        "pageSize": args.page_size,
        "pageNo": args.page_no,
    }
    if args.status:
        params["status"] = args.status
    if args.token:
        params["token"] = args.token
    handle_response(trade_get("/v1/thirdParty/tx/getLimitOrder", params, proxy=True))


def cmd_cancel_limit_order(args):
    payload = {"chain": args.chain, "ids": args.ids}
    handle_response(trade_post("/v1/thirdParty/tx/cancelLimitOrder", payload, proxy=True))


def cmd_approve_token(args):
    payload = {
        "chain": args.chain,
        "assetsId": args.assets_id,
        "tokenAddress": args.token_address,
    }
    handle_response(trade_post("/v1/thirdParty/tx/approve", payload, proxy=True))


def cmd_get_approval(args):
    handle_response(trade_get(
        "/v1/thirdParty/tx/getApprove", {"chain": args.chain, "ids": args.ids}, proxy=True
    ))


def cmd_transfer(args):
    payload = {
        "chain": args.chain,
        "assetsId": args.assets_id,
        "fromAddress": args.from_address,
        "toAddress": args.to_address,
        "tokenAddress": args.token_address,
        "amount": args.amount,
    }
    if args.gas:
        payload["gas"] = args.gas
    if args.extra_gas:
        payload["extraGas"] = args.extra_gas
    handle_response(trade_post("/v1/thirdParty/tx/transfer", payload, proxy=True))


def cmd_get_transfer(args):
    handle_response(trade_get(
        "/v1/thirdParty/tx/getTransfer", {"chain": args.chain, "ids": args.ids}, proxy=True
    ))


def main():
    if not IN_SERVER:
        _docker_gate("ave_trade_rest.py")

    parser = argparse.ArgumentParser(description="AVE Cloud Trade REST API client")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("quote", help="Get swap quote (estimated output)")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])

    p = sub.add_parser("create-evm-tx", help="Create unsigned EVM swap transaction")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--creator-address", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")

    p = sub.add_parser("send-evm-tx", help="Submit signed EVM transaction")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--request-tx-id", required=True)
    p.add_argument("--signed-tx", required=True)
    p.add_argument("--use-mev", action="store_true")

    p = sub.add_parser("create-solana-tx", help="Create unsigned Solana swap transaction")
    p.add_argument("--creator-address", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee", required=True)
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")

    p = sub.add_parser("send-solana-tx", help="Submit signed Solana transaction")
    p.add_argument("--request-tx-id", required=True)
    p.add_argument("--signed-tx", required=True)
    p.add_argument("--use-mev", action="store_true")

    p = sub.add_parser("swap-evm", help="One-step EVM swap: create + sign + send (requires key/mnemonic)")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--rpc-url", default=None, help="Required EVM JSON-RPC URL for local signing metadata (overrides AVE_BSC_RPC_URL/AVE_ETH_RPC_URL/AVE_BASE_RPC_URL env)")

    p = sub.add_parser("swap-solana", help="One-step Solana swap: create + sign + send (requires key/mnemonic)")
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee", required=True)
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--use-mev", action="store_true")

    p = sub.add_parser("list-wallets", help="List proxy wallets")
    p.add_argument("--assets-ids", default=None, help="Comma-separated asset IDs to filter by")

    p = sub.add_parser("create-wallet", help="Create a delegate proxy wallet")
    p.add_argument("--name", required=True)
    p.add_argument("--return-mnemonic", action="store_true")

    p = sub.add_parser("delete-wallet", help="Delete delegate proxy wallets")
    p.add_argument("--assets-ids", required=True, nargs="+")

    p = sub.add_parser("market-order", help="Place a market swap order")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--gas", default=None)
    p.add_argument("--extra-gas", default=None)
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--auto-gas", default=None, choices=["low", "average", "high"])
    p.add_argument(
        "--auto-sell", action="append", default=None, metavar="JSON",
        help='Auto-sell rule as JSON (repeatable, max 10 default + 1 trailing). '
             'E.g.: \'{"priceChange":"-5000","sellRatio":"10000","type":"default"}\''
    )

    p = sub.add_parser("limit-order", help="Place a limit order")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--limit-price", required=True)
    p.add_argument("--gas", default=None)
    p.add_argument("--extra-gas", default=None)
    p.add_argument("--expire-time", default=None)
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--auto-gas", default=None, choices=["low", "average", "high"])

    p = sub.add_parser("get-swap-orders", help="Query market swap orders by IDs")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--ids", required=True, help="Comma-separated order IDs")

    p = sub.add_parser("get-limit-orders", help="Query limit orders (paginated)")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--page-size", required=True)
    p.add_argument("--page-no", required=True)
    p.add_argument("--status", default=None,
                   choices=["waiting", "confirmed", "error", "auto_cancelled", "cancelled"])
    p.add_argument("--token", default=None)

    p = sub.add_parser("cancel-limit-order", help="Cancel pending limit orders")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--ids", required=True, nargs="+")

    p = sub.add_parser("approve-token", help="Approve token for EVM proxy wallet trading")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--token-address", required=True)

    p = sub.add_parser("get-approval", help="Query token approval status")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--ids", required=True, help="Comma-separated approval order IDs")

    p = sub.add_parser("transfer", help="Transfer tokens from a delegate proxy wallet")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--from-address", required=True)
    p.add_argument("--to-address", required=True)
    p.add_argument("--token-address", required=True)
    p.add_argument("--amount", required=True)
    p.add_argument("--gas", default=None)
    p.add_argument("--extra-gas", default=None)

    p = sub.add_parser("get-transfer", help="Query transfer status")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--ids", required=True, help="Comma-separated transfer order IDs")

    args = parser.parse_args()

    commands = {
        "quote": cmd_quote,
        "create-evm-tx": cmd_create_evm_tx,
        "send-evm-tx": cmd_send_evm_tx,
        "create-solana-tx": cmd_create_solana_tx,
        "send-solana-tx": cmd_send_solana_tx,
        "swap-evm": cmd_swap_evm,
        "swap-solana": cmd_swap_solana,
        "list-wallets": cmd_list_wallets,
        "create-wallet": cmd_create_wallet,
        "delete-wallet": cmd_delete_wallet,
        "market-order": cmd_market_order,
        "limit-order": cmd_limit_order,
        "get-swap-orders": cmd_get_swap_orders,
        "get-limit-orders": cmd_get_limit_orders,
        "cancel-limit-order": cmd_cancel_limit_order,
        "approve-token": cmd_approve_token,
        "get-approval": cmd_get_approval,
        "transfer": cmd_transfer,
        "get-transfer": cmd_get_transfer,
    }

    try:
        commands[args.command](args)
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
