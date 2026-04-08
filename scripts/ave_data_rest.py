#!/usr/bin/env python3
"""AVE Cloud Data REST API client CLI.

Usage: python ave_data_rest.py <command> [options]
Requires: AVE_API_KEY and API_PLAN environment variables
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

V2_BASE = "https://data.ave-api.xyz/v2"
WSS_BASE = "wss://wss.ave-api.xyz"
VALID_WSS_INTERVALS = ("s1", "k1", "k5", "k15", "k30", "k60", "k120", "k240", "k1440", "k10080")

VALID_PLANS = ("free", "normal", "pro")

VALID_PLATFORMS = (
    "alpha", "bsc_hot", "gold", "hot", "inclusion", "meme", "new",
    "bn_in_almost", "bn_in_hot", "bn_in_new", "bn_out_hot", "bn_out_new",
    "bankr_in_almost", "bankr_in_new", "bankr_out_new",
    "baseapp_in_almost", "baseapp_in_new", "baseapp_out_new",
    "basememe_in_almost", "basememe_in_new", "basememe_out_new",
    "bonk_in_almost", "bonk_in_hot", "bonk_in_new", "bonk_out_hot", "bonk_out_new",
    "boop_in_almost", "boop_in_hot", "boop_in_new", "boop_out_hot", "boop_out_new",
    "clanker_in_almost", "clanker_in_new", "clanker_out_new",
    "cookpump_in_almost", "cookpump_in_hot", "cookpump_in_new", "cookpump_out_hot", "cookpump_out_new",
    "flap_in_almost", "flap_in_hot", "flap_in_new", "flap_out_hot", "flap_out_new",
    "fourmeme_in_almost", "fourmeme_in_hot", "fourmeme_in_new", "fourmeme_out_hot", "fourmeme_out_new",
    "grafun_in_almost", "grafun_in_hot", "grafun_in_new", "grafun_out_hot", "grafun_out_new",
    "heaven_in_almost", "heaven_in_new", "heaven_out_hot",
    "klik_in_almost", "klik_in_new", "klik_out_new",
    "meteora_in_hot", "meteora_in_new", "meteora_out_hot", "meteora_out_new",
    "moonshot_in_hot", "moonshot_out_hot",
    "movepump_in_hot", "movepump_out_hot",
    "nadfun_in_almost", "nadfun_in_hot", "nadfun_in_new", "nadfun_out_hot", "nadfun_out_new",
    "popme_in_new", "popme_out_new",
    "pump_all_in_almost", "pump_all_in_hot", "pump_all_in_new", "pump_all_out_hot", "pump_all_out_new",
    "pump_in_almost", "pump_in_hot", "pump_in_new", "pump_out_hot", "pump_out_new",
    "sunpump_in_almost", "sunpump_in_hot", "sunpump_in_new", "sunpump_out_hot", "sunpump_out_new",
    "xdyorswap_in_hot", "xdyorswap_in_new", "xdyorswap_out_hot", "xdyorswap_out_new",
    "xflap_in_almost", "xflap_in_hot", "xflap_in_new", "xflap_out_hot", "xflap_out_new",
    "zoracontent_in_almost", "zoracontent_in_new", "zoracontent_out_new",
    "zoracreator_in_almost", "zoracreator_in_new", "zoracreator_out_new",
)

PLAN_RPS = {"free": 1, "normal": 5, "pro": 20}
PLAN_MIN_INTERVAL = {"free": 1.0, "normal": 0.2, "pro": 0.05}
RATE_LIMIT_FILE = "/tmp/ave_client_last_request"

USE_DOCKER = os.environ.get("AVE_USE_DOCKER", "").lower() in ("1", "true", "yes")
IN_SERVER = os.environ.get("AVE_IN_SERVER", "").lower() in ("1", "true", "yes")
SERVER_CONTAINER = "ave-cloud-server"
SERVER_FIFO = "/tmp/ave_pipe"

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
            "Get a free key at https://cloud.ave.ai/register | Support: https://t.me/ave_ai_cloud"
        )
    return key


def get_api_plan():
    plan = os.environ.get("API_PLAN", "free")
    if plan not in VALID_PLANS:
        raise ValueError(f"API_PLAN must be one of: {', '.join(VALID_PLANS)}")
    return plan


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
    with open(RATE_LIMIT_FILE, "a+") as f:
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


def _headers():
    return {"X-API-KEY": get_api_key(), "Content-Type": "application/json"}


class _Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    @property
    def text(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise urllib.error.HTTPError(None, self.status_code, f"HTTP {self.status_code}", {}, None)

    def json(self):
        return json.loads(self._body)


def _urllib_get(url):
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req) as resp:
            return _Response(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return _Response(e.code, body)


def _urllib_post(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return _Response(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return _Response(e.code, body)


def api_get(path, params=None):
    url = f"{V2_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    if IN_SERVER:
        return _get_session().get(url, headers=_headers())
    _builtin_rate_limit()
    return _urllib_get(url)


def api_post(path, payload):
    url = f"{V2_BASE}{path}"
    if IN_SERVER:
        return _get_session().post(url, headers=_headers(), json=payload)
    _builtin_rate_limit()
    return _urllib_post(url, payload)


def handle_response(resp):
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    print(json.dumps(resp.json(), indent=2))


def _server_is_running():
    r = subprocess.run(
        ["docker", "inspect", "--format={{.State.Running}}", SERVER_CONTAINER],
        capture_output=True, text=True,
    )
    return r.returncode == 0 and r.stdout.strip() == "true"


def _exec_in_server(argv):
    result = subprocess.run(
        ["docker", "exec", SERVER_CONTAINER, "python", "scripts/ave_data_rest.py"] + list(argv),
    )
    sys.exit(result.returncode)


def cmd_search(args):
    params = {"keyword": args.keyword, "limit": args.limit}
    if args.chain:
        params["chain"] = args.chain
    if args.orderby:
        params["orderby"] = args.orderby
    handle_response(api_get("/tokens", params))


def cmd_platform_tokens(args):
    params = {"tag": args.platform}
    if args.limit:
        params["limit"] = args.limit
    if args.orderby:
        params["orderby"] = args.orderby
    handle_response(api_get("/tokens/platform", params))


def cmd_token(args):
    handle_response(api_get(f"/tokens/{args.address}-{args.chain}"))


def cmd_price(args):
    evm_chains = ("-bsc", "-eth", "-base")
    payload = {"token_ids": [token.lower() if token.endswith(evm_chains) else token for token in args.tokens]}
    if args.tvl_min:
        payload["tvl_min"] = int(args.tvl_min) if args.tvl_min.is_integer() else args.tvl_min
    if args.volume_min:
        payload["tx_24h_volume_min"] = int(args.volume_min) if args.volume_min.is_integer() else args.volume_min
    handle_response(api_post("/tokens/price", payload))


def cmd_kline_token(args):
    params = {"interval": args.interval, "limit": args.size}
    resp = api_get(f"/klines/token/{args.address}-{args.chain}", params)
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    body = resp.json()
    points = body.get("data", {}).get("points")
    if isinstance(points, list) and len(points) > args.size:
        body["data"]["points"] = points[-args.size:]
        body["data"]["limit"] = args.size
        body["data"]["total_count"] = len(body["data"]["points"])
    print(json.dumps(body, indent=2))


def cmd_kline_pair(args):
    params = {"interval": args.interval, "limit": args.size}
    resp = api_get(f"/klines/pair/{args.address}-{args.chain}", params)
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    body = resp.json()
    points = body.get("data", {}).get("points")
    if isinstance(points, list) and len(points) > args.size:
        body["data"]["points"] = points[-args.size:]
        body["data"]["limit"] = args.size
        body["data"]["total_count"] = len(body["data"]["points"])
    print(json.dumps(body, indent=2))


def cmd_kline_ondo(args):
    params = {"interval": args.interval, "limit": args.size}
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.to_time is not None:
        params["to_time"] = args.to_time
    resp = api_get(f"/klines/pair/ondo/{args.pair}", params)
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


def cmd_holders(args):
    params = {}
    if args.limit:
        params["limit"] = args.limit
    if args.sort_by:
        params["sort_by"] = args.sort_by
    if args.order:
        params["order"] = args.order
    handle_response(api_get(f"/tokens/holders/{args.address}-{args.chain}", params))


def cmd_search_details(args):
    if len(args.tokens) > 50:
        print("Error: max 50 tokens per request", file=sys.stderr)
        sys.exit(1)
    payload = {"token_ids": args.tokens}
    handle_response(api_post("/tokens/search", payload))


def cmd_txs(args):
    handle_response(api_get(f"/txs/{args.address}-{args.chain}"))


def cmd_trending(args):
    params = {"chain": args.chain, "current_page": args.page, "page_size": args.page_size}
    handle_response(api_get("/tokens/trending", params))


def cmd_rank_topics(args):
    handle_response(api_get("/ranks/topics"))


def cmd_ranks(args):
    handle_response(api_get("/ranks", {"topic": args.topic}))


def cmd_risk(args):
    handle_response(api_get(f"/contracts/{args.address}-{args.chain}"))


def cmd_chains(args):
    handle_response(api_get("/supported_chains"))


def cmd_main_tokens(args):
    handle_response(api_get("/tokens/main", {"chain": args.chain}))


def cmd_address_txs(args):
    params = {"wallet_address": args.wallet, "chain": args.chain}
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
    handle_response(api_get("/address/tx", params))


def cmd_address_pnl(args):
    params = {
        "wallet_address": args.wallet,
        "chain": args.chain,
        "token_address": args.token,
    }
    handle_response(api_get("/address/pnl", params))


def cmd_wallet_tokens(args):
    params = {"wallet_address": args.wallet, "chain": args.chain}
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
    handle_response(api_get("/address/walletinfo/tokens", params))


def cmd_wallet_info(args):
    params = {"wallet_address": args.wallet, "chain": args.chain}
    if args.self_address:
        params["self_address"] = args.self_address
    handle_response(api_get("/address/walletinfo", params))


def cmd_smart_wallets(args):
    params = {"chain": args.chain}
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
    handle_response(api_get("/address/smart_wallet/list", params))


def cmd_signals(args):
    params = {"chain": args.chain, "pageSize": args.page_size, "pageNO": args.page_no}
    handle_response(api_get("/signals/public/list", params))


def cmd_liq_txs(args):
    params = {"limit": args.limit, "sort": args.sort}
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.to_time is not None:
        params["to_time"] = args.to_time
    if args.type:
        params["type"] = args.type
    handle_response(api_get(f"/txs/liq/{args.address}-{args.chain}", params))


def cmd_tx_detail(args):
    params = {
        "chain": args.chain,
        "account_address": args.account,
        "tx_hash": args.tx_hash,
    }
    if args.start_from is not None:
        params["start_from"] = args.start_from
    if args.end_at is not None:
        params["end_at"] = args.end_at
    if args.limit:
        params["limit"] = args.limit
    handle_response(api_get("/txs/detail", params))


def cmd_pair(args):
    handle_response(api_get(f"/pairs/{args.address}-{args.chain}"))


def main():
    if not IN_SERVER:
        _docker_gate("ave_data_rest.py")

    parser = argparse.ArgumentParser(description="AVE Cloud Data REST API client")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="Search tokens by keyword")
    p.add_argument("--keyword", required=True)
    p.add_argument("--chain", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--orderby", default=None,
                   choices=["tx_volume_u_24h", "main_pair_tvl", "fdv", "market_cap"])

    p = sub.add_parser("platform-tokens", help="Get tokens by platform/launchpad tag")
    p.add_argument("--platform", required=True, choices=VALID_PLATFORMS)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--orderby", default=None, choices=["tx_volume_u_24h", "main_pair_tvl"])

    p = sub.add_parser("token", help="Get token detail")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

    p = sub.add_parser("price", help="Get prices for up to 200 tokens")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN")
    p.add_argument("--tvl-min", type=float, default=None)
    p.add_argument("--volume-min", type=float, default=None)

    p = sub.add_parser("kline-token", help="Get kline data by token address")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", type=int, default=60,
                   choices=[1, 5, 15, 30, 60, 120, 240, 1440, 4320, 10080])
    p.add_argument("--size", type=int, default=24)

    p = sub.add_parser("kline-pair", help="Get kline data by pair address")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", type=int, default=60,
                   choices=[1, 5, 15, 30, 60, 120, 240, 1440, 4320, 10080])
    p.add_argument("--size", type=int, default=24)

    p = sub.add_parser("kline-ondo", help="Get Ondo-mapped kline data by pair address or ticker")
    p.add_argument("--pair", required=True, help="pair_address-chain or ticker symbol")
    p.add_argument("--interval", type=int, default=60, choices=[1, 5, 15, 60, 240, 720, 1440])
    p.add_argument("--size", type=int, default=24)
    p.add_argument("--from-time", type=int, default=None)
    p.add_argument("--to-time", type=int, default=None)

    p = sub.add_parser("holders", help="Get token holders with sort/order")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--sort-by", default="balance", choices=["balance", "percentage"])
    p.add_argument("--order", default="desc", choices=["asc", "desc"])

    p = sub.add_parser("search-details", help="Batch search token details by address-chain list")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN",
                   help="Up to 50 address-chain identifiers")

    p = sub.add_parser("txs", help="Get swap transactions for a pair")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

    p = sub.add_parser("trending", help="Get trending tokens on a chain")
    p.add_argument("--chain", required=True)
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--page-size", type=int, default=20)

    sub.add_parser("rank-topics", help="List available rank topics")

    p = sub.add_parser("ranks", help="Get token rankings by topic")
    p.add_argument("--topic", required=True)

    p = sub.add_parser("risk", help="Get contract risk/security report")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

    sub.add_parser("chains", help="List all supported chains")

    p = sub.add_parser("main-tokens", help="Get main tokens for a chain")
    p.add_argument("--chain", required=True)

    p = sub.add_parser("address-txs", help="Get wallet swap transaction history")
    p.add_argument("--wallet", required=True, help="Wallet address")
    p.add_argument("--chain", required=True)
    p.add_argument("--token", default=None, help="Filter by token address")
    p.add_argument("--from-time", type=int, default=None, help="Unix timestamp start")
    p.add_argument("--last-time", default=None, help="RFC3339 cursor for pagination")
    p.add_argument("--last-id", default=None, help="Cursor ID for pagination")
    p.add_argument("--page-size", type=int, default=None, help="Results per page (max 100)")

    p = sub.add_parser("address-pnl", help="Get wallet PnL for a specific token")
    p.add_argument("--wallet", required=True, help="Wallet address")
    p.add_argument("--chain", required=True)
    p.add_argument("--token", required=True, help="Token contract address")

    p = sub.add_parser("wallet-tokens", help="Get token holdings for a wallet")
    p.add_argument("--wallet", required=True, help="Wallet address")
    p.add_argument("--chain", required=True)
    p.add_argument("--sort", default=None, help="Sort field (default: last_txn_time)")
    p.add_argument("--sort-dir", default=None, choices=["asc", "desc"])
    p.add_argument("--page-size", type=int, default=None)
    p.add_argument("--page-no", type=int, default=None)
    p.add_argument("--hide-sold", action="store_true", help="Hide tokens with zero balance")
    p.add_argument("--hide-small", type=float, default=None, help="Hide tokens below USD value")
    p.add_argument("--blue-chips", action="store_true", help="Only show blue-chip tokens")

    p = sub.add_parser("wallet-info", help="Get wallet overview and stats")
    p.add_argument("--wallet", required=True, help="Wallet address to inspect")
    p.add_argument("--chain", required=True)
    p.add_argument("--self-address", default=None, help="Your own address for relative stats")

    p = sub.add_parser("smart-wallets", help="List smart wallets with profit filters")
    p.add_argument("--chain", required=True)
    p.add_argument("--keyword", default=None, help="Search by address keyword")
    p.add_argument("--sort", default=None)
    p.add_argument("--sort-dir", default=None, choices=["asc", "desc"])
    p.add_argument("--profit-above-900-percent-num-min", type=float, default=None, dest="profit_above_900_percent_num_min")
    p.add_argument("--profit-above-900-percent-num-max", type=float, default=None, dest="profit_above_900_percent_num_max")
    p.add_argument("--profit-300-900-percent-num-min", type=float, default=None, dest="profit_300_900_percent_num_min")
    p.add_argument("--profit-300-900-percent-num-max", type=float, default=None, dest="profit_300_900_percent_num_max")
    p.add_argument("--profit-100-300-percent-num-min", type=float, default=None, dest="profit_100_300_percent_num_min")
    p.add_argument("--profit-100-300-percent-num-max", type=float, default=None, dest="profit_100_300_percent_num_max")
    p.add_argument("--profit-10-100-percent-num-min", type=float, default=None, dest="profit_10_100_percent_num_min")
    p.add_argument("--profit-10-100-percent-num-max", type=float, default=None, dest="profit_10_100_percent_num_max")
    p.add_argument("--profit-neg10-10-percent-num-min", type=float, default=None, dest="profit_neg10_10_percent_num_min")
    p.add_argument("--profit-neg10-10-percent-num-max", type=float, default=None, dest="profit_neg10_10_percent_num_max")
    p.add_argument("--profit-neg50-neg10-percent-num-min", type=float, default=None, dest="profit_neg50_neg10_percent_num_min")
    p.add_argument("--profit-neg50-neg10-percent-num-max", type=float, default=None, dest="profit_neg50_neg10_percent_num_max")
    p.add_argument("--profit-neg100-neg50-percent-num-min", type=float, default=None, dest="profit_neg100_neg50_percent_num_min")
    p.add_argument("--profit-neg100-neg50-percent-num-max", type=float, default=None, dest="profit_neg100_neg50_percent_num_max")
    p.add_argument("--last-trade-time-min", type=float, default=None, dest="last_trade_time_min")
    p.add_argument("--last-trade-time-max", type=float, default=None, dest="last_trade_time_max")

    p = sub.add_parser("signals", help="Get public trading signals")
    p.add_argument("--chain", default="solana")
    p.add_argument("--page-size", type=int, default=10)
    p.add_argument("--page-no", type=int, default=1)

    p = sub.add_parser("liq-txs", help="Get liquidity transactions for a pair")
    p.add_argument("--address", required=True, help="Pair address")
    p.add_argument("--chain", required=True)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--from-time", type=int, default=None, help="Unix timestamp start")
    p.add_argument("--to-time", type=int, default=None, help="Unix timestamp end")
    p.add_argument("--type", default="all",
                   choices=["addLiquidity", "removeLiquidity", "createPair", "all"])
    p.add_argument("--sort", default="asc", choices=["asc", "desc"])

    p = sub.add_parser("tx-detail", help="Get transaction detail by hash")
    p.add_argument("--chain", required=True)
    p.add_argument("--account", required=True, help="Account address involved in the tx")
    p.add_argument("--tx-hash", required=True, help="Transaction hash")
    p.add_argument("--start-from", type=int, default=None, help="Unix timestamp range start")
    p.add_argument("--end-at", type=int, default=None, help="Unix timestamp range end")
    p.add_argument("--limit", type=int, default=None)

    p = sub.add_parser("pair", help="Get trading pair detail")
    p.add_argument("--address", required=True, help="Pair contract address")
    p.add_argument("--chain", required=True)

    if not IN_SERVER:
        _docker_gate("ave_data_rest.py")

    args = parser.parse_args()

    commands = {
        "search": cmd_search,
        "token": cmd_token,
        "price": cmd_price,
        "kline-token": cmd_kline_token,
        "kline-pair": cmd_kline_pair,
        "kline-ondo": cmd_kline_ondo,
        "holders": cmd_holders,
        "search-details": cmd_search_details,
        "txs": cmd_txs,
        "platform-tokens": cmd_platform_tokens,
        "trending": cmd_trending,
        "rank-topics": cmd_rank_topics,
        "ranks": cmd_ranks,
        "risk": cmd_risk,
        "chains": cmd_chains,
        "main-tokens": cmd_main_tokens,
        "address-txs": cmd_address_txs,
        "address-pnl": cmd_address_pnl,
        "wallet-tokens": cmd_wallet_tokens,
        "wallet-info": cmd_wallet_info,
        "smart-wallets": cmd_smart_wallets,
        "signals": cmd_signals,
        "liq-txs": cmd_liq_txs,
        "tx-detail": cmd_tx_detail,
        "pair": cmd_pair,
    }

    try:
        commands[args.command](args)
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
