#!/usr/bin/env python3
"""AVE Cloud Data API client CLI.

Usage: python ave_client.py <command> [options]
Requires: AVE_API_KEY and API_PLAN environment variables
"""

import argparse
import fcntl
import json
import os
import shlex
import subprocess
import sys
import threading
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

# Set AVE_USE_DOCKER=true to use requests + requests-ratelimiter (installed in Docker).
# Default (false): uses stdlib urllib with built-in file-based rate limiter.
USE_DOCKER = os.environ.get("AVE_USE_DOCKER", "").lower() in ("1", "true", "yes")
IN_SERVER = os.environ.get("AVE_IN_SERVER", "").lower() in ("1", "true", "yes")
SERVER_CONTAINER = "ave-cloud-server"
SERVER_FIFO = "/tmp/ave_pipe"


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
    """Build a requests session with rate limiting via requests-ratelimiter."""
    try:
        import warnings
        warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
        from requests_ratelimiter import LimiterSession
    except ImportError:
        raise ImportError(
            "requests or requests-ratelimiter is not installed. "
            "Run: pip install -r scripts/requirements.txt "
            "Or unset AVE_USE_DOCKER to use the built-in urllib mode."
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
    """Enforce per-plan RPS limit across CLI invocations using a shared timestamp file."""
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
    """Minimal response wrapper for urllib responses."""
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
    if USE_DOCKER:
        return _get_session().get(url, headers=_headers())
    _builtin_rate_limit()
    return _urllib_get(url)


def api_post(path, payload):
    url = f"{V2_BASE}{path}"
    if USE_DOCKER:
        return _get_session().post(url, headers=_headers(), json=payload)
    _builtin_rate_limit()
    return _urllib_post(url, payload)


def handle_response(resp):
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    print(json.dumps(resp.json(), indent=2))


def _require_pro():
    if get_api_plan() != "pro":
        print("Error: WebSocket subscriptions require API_PLAN=pro.", file=sys.stderr)
        sys.exit(1)


def _require_docker():
    if not USE_DOCKER:
        print("Error: API_PLAN=pro requires AVE_USE_DOCKER=true.", file=sys.stderr)
        sys.exit(1)


def _server_is_running():
    r = subprocess.run(
        ["docker", "inspect", "--format={{.State.Running}}", SERVER_CONTAINER],
        capture_output=True, text=True,
    )
    return r.returncode == 0 and r.stdout.strip() == "true"


def _exec_in_server(argv):
    """Run a REST command inside the server container; stream output to host."""
    result = subprocess.run(
        ["docker", "exec", SERVER_CONTAINER, "python", "scripts/ave_client.py"] + list(argv),
    )
    sys.exit(result.returncode)


def _send_to_server(line):
    """Write a subscribe/unsubscribe line to the server's FIFO."""
    result = subprocess.run(
        ["docker", "exec", SERVER_CONTAINER, "sh", "-c",
         f"echo {shlex.quote(line)} > {SERVER_FIFO}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error sending to server: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Sent. Watch events: docker logs -f {SERVER_CONTAINER}", file=sys.stderr)


def _wss_on_message(ws, message):
    try:
        print(json.dumps(json.loads(message), indent=2), flush=True)
        print("---", flush=True)
    except json.JSONDecodeError:
        print(message, flush=True)


def _wss_connect(on_open):
    _require_pro()
    try:
        import websocket
    except ImportError:
        print(
            "Error: websocket-client is not installed.\n"
            "Run: pip install -r scripts/requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    def on_error(ws, error):
        print(f"WebSocket error: {error}", file=sys.stderr)

    def on_close(ws, close_status_code, close_msg):
        print("\nConnection closed.", file=sys.stderr)

    ws = websocket.WebSocketApp(
        WSS_BASE,
        header={"X-API-KEY": get_api_key()},
        on_open=on_open,
        on_message=_wss_on_message,
        on_error=on_error,
        on_close=on_close,
    )
    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except KeyboardInterrupt:
        ws.close()


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
    payload = {"token_ids": args.tokens}
    if args.tvl_min:
        payload["tvl_min"] = args.tvl_min
    if args.volume_min:
        payload["tx_24h_volume_min"] = args.volume_min
    handle_response(api_post("/tokens/price", payload))


def cmd_kline_token(args):
    params = {"interval": args.interval, "size": args.size}
    handle_response(api_get(f"/klines/token/{args.address}-{args.chain}", params))


def cmd_kline_pair(args):
    params = {"interval": args.interval, "size": args.size}
    handle_response(api_get(f"/klines/pair/{args.address}-{args.chain}", params))


def cmd_holders(args):
    handle_response(api_get(f"/tokens/top100/{args.address}-{args.chain}"))


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


def cmd_watch_tx(args):
    def on_open(ws):
        ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": [args.topic, args.address, args.chain], "id": 1,
        }))
    _wss_connect(on_open)


def cmd_watch_kline(args):
    def on_open(ws):
        ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": ["kline", args.address, args.interval, args.chain], "id": 1,
        }))
    _wss_connect(on_open)


def cmd_watch_price(args):
    def on_open(ws):
        ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": ["price", args.tokens], "id": 1,
        }))
    _wss_connect(on_open)


def cmd_wss_repl(args):
    _require_pro()
    try:
        import websocket
    except ImportError:
        print(
            "Error: websocket-client is not installed.\n"
            "Run: pip install -r scripts/requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    ws_ref = [None]
    connected = threading.Event()
    msg_id = [0]

    def next_id():
        msg_id[0] += 1
        return msg_id[0]

    def on_open(ws):
        ws_ref[0] = ws
        connected.set()

    def on_error(ws, error):
        print(f"\nWebSocket error: {error}", file=sys.stderr)

    def on_close(ws, close_status_code, close_msg):
        print("\nConnection closed.", file=sys.stderr)
        connected.clear()

    ws = websocket.WebSocketApp(
        WSS_BASE,
        header={"X-API-KEY": get_api_key()},
        on_open=on_open,
        on_message=_wss_on_message,
        on_error=on_error,
        on_close=on_close,
    )
    t = threading.Thread(
        target=ws.run_forever,
        kwargs={"ping_interval": 30, "ping_timeout": 10},
        daemon=True,
    )
    t.start()

    if not connected.wait(timeout=10):
        print("Error: failed to connect within 10s.", file=sys.stderr)
        sys.exit(1)

    print("Connected. Type 'help' for commands.", file=sys.stderr)

    try:
        while True:
            try:
                line = input("\n> ").strip()
            except EOFError:
                break
            if not line:
                continue
            parts = line.split()
            cmd = parts[0].lower()

            if cmd in ("quit", "exit", "q"):
                break
            elif cmd == "help":
                print(
                    "Commands:\n"
                    "  subscribe price <addr-chain> [<addr-chain> ...]\n"
                    "  subscribe tx <pair_address> <chain> [tx|multi_tx|liq]\n"
                    "  subscribe kline <pair_address> <chain> [interval]\n"
                    "  unsubscribe\n"
                    "  quit",
                    file=sys.stderr,
                )
            elif cmd == "subscribe":
                if len(parts) < 2:
                    print("Usage: subscribe <topic> [args...]", file=sys.stderr)
                    continue
                topic = parts[1]
                if topic == "price":
                    tokens = parts[2:]
                    if not tokens:
                        print("Usage: subscribe price <addr-chain> [...]", file=sys.stderr)
                        continue
                    ws_ref[0].send(json.dumps({
                        "jsonrpc": "2.0", "method": "subscribe",
                        "params": ["price", tokens], "id": next_id(),
                    }))
                elif topic in ("tx", "multi_tx", "liq"):
                    if len(parts) < 4:
                        print("Usage: subscribe tx|multi_tx|liq <pair_address> <chain>", file=sys.stderr)
                        continue
                    address, chain = parts[2], parts[3]
                    ws_ref[0].send(json.dumps({
                        "jsonrpc": "2.0", "method": "subscribe",
                        "params": [topic, address, chain], "id": next_id(),
                    }))
                elif topic == "kline":
                    if len(parts) < 4:
                        print("Usage: subscribe kline <pair_address> <chain> [interval]", file=sys.stderr)
                        continue
                    address, chain = parts[2], parts[3]
                    interval = parts[4] if len(parts) > 4 else "k60"
                    ws_ref[0].send(json.dumps({
                        "jsonrpc": "2.0", "method": "subscribe",
                        "params": ["kline", address, interval, chain], "id": next_id(),
                    }))
                else:
                    print(f"Unknown topic: {topic!r}. Topics: price, tx, multi_tx, liq, kline", file=sys.stderr)
            elif cmd == "unsubscribe":
                ws_ref[0].send(json.dumps({
                    "jsonrpc": "2.0", "method": "unsubscribe",
                    "params": [], "id": next_id(),
                }))
            else:
                print(f"Unknown command: {cmd!r}. Type 'help'.", file=sys.stderr)
    except KeyboardInterrupt:
        pass
    finally:
        ws.close()


def cmd_serve(args):
    _require_pro()
    try:
        import websocket
    except ImportError:
        print("Error: websocket-client is not installed.", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(SERVER_FIFO):
        os.remove(SERVER_FIFO)
    os.mkfifo(SERVER_FIFO)

    ws_ref = [None]
    connected = threading.Event()
    msg_id = [0]

    def next_id():
        msg_id[0] += 1
        return msg_id[0]

    def on_open(ws):
        ws_ref[0] = ws
        connected.set()

    def on_error(ws, error):
        print(f"WebSocket error: {error}", file=sys.stderr, flush=True)

    def on_close(ws, code, msg):
        print("WebSocket closed.", file=sys.stderr, flush=True)
        connected.clear()

    ws = websocket.WebSocketApp(
        WSS_BASE,
        header={"X-API-KEY": get_api_key()},
        on_open=on_open,
        on_message=_wss_on_message,
        on_error=on_error,
        on_close=on_close,
    )
    t = threading.Thread(
        target=ws.run_forever,
        kwargs={"ping_interval": 30, "ping_timeout": 10},
        daemon=True,
    )
    t.start()

    if not connected.wait(timeout=10):
        print("Error: WebSocket connection timeout.", file=sys.stderr)
        sys.exit(1)

    print("Server ready.", file=sys.stderr, flush=True)

    def _process_cmd(line):
        parts = line.split()
        if not parts:
            return
        cmd = parts[0].lower()
        if cmd == "subscribe" and len(parts) >= 2:
            topic = parts[1]
            if topic == "price" and len(parts) >= 3:
                ws_ref[0].send(json.dumps({
                    "jsonrpc": "2.0", "method": "subscribe",
                    "params": ["price", parts[2:]], "id": next_id(),
                }))
            elif topic in ("tx", "multi_tx", "liq") and len(parts) >= 4:
                ws_ref[0].send(json.dumps({
                    "jsonrpc": "2.0", "method": "subscribe",
                    "params": [topic, parts[2], parts[3]], "id": next_id(),
                }))
            elif topic == "kline" and len(parts) >= 4:
                interval = parts[4] if len(parts) > 4 else "k60"
                ws_ref[0].send(json.dumps({
                    "jsonrpc": "2.0", "method": "subscribe",
                    "params": ["kline", parts[2], interval, parts[3]], "id": next_id(),
                }))
            print(f"Subscribed: {' '.join(parts[1:])}", file=sys.stderr, flush=True)
        elif cmd == "unsubscribe":
            ws_ref[0].send(json.dumps({
                "jsonrpc": "2.0", "method": "unsubscribe",
                "params": [], "id": next_id(),
            }))
            print("Unsubscribed.", file=sys.stderr, flush=True)

    try:
        while True:
            with open(SERVER_FIFO, "r") as pipe:
                for raw in pipe:
                    _process_cmd(raw.strip())
    except KeyboardInterrupt:
        ws.close()


def cmd_start_server(args):
    _require_pro()
    _require_docker()
    if _server_is_running():
        print(f"Server already running: {SERVER_CONTAINER}", file=sys.stderr)
        return
    subprocess.run(["docker", "rm", "-f", SERVER_CONTAINER], capture_output=True)
    key = get_api_key()
    result = subprocess.run([
        "docker", "run", "-d", "--name", SERVER_CONTAINER,
        "-e", f"AVE_API_KEY={key}",
        "-e", "API_PLAN=pro",
        "-e", "AVE_USE_DOCKER=true",
        "-e", "AVE_IN_SERVER=true",
        "ave-cloud", "serve",
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Started ({result.stdout.strip()[:12]}). Logs: docker logs -f {SERVER_CONTAINER}",
          file=sys.stderr)


def cmd_stop_server(args):
    result = subprocess.run(
        ["docker", "rm", "-f", SERVER_CONTAINER], capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Server stopped: {SERVER_CONTAINER}", file=sys.stderr)
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AVE Cloud Data API client")
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

    p = sub.add_parser("holders", help="Get top 100 holders")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

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

    p = sub.add_parser("watch-tx", help="Stream live swap/liquidity events (pro plan)")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--topic", default="tx", choices=["tx", "multi_tx", "liq"])

    p = sub.add_parser("watch-kline", help="Stream live kline updates for a pair (pro plan)")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", default="k60", choices=list(VALID_WSS_INTERVALS))

    p = sub.add_parser("watch-price", help="Stream live price changes for tokens (pro plan)")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN")

    sub.add_parser("wss-repl", help="Interactive WebSocket REPL — subscribe/unsubscribe on demand (pro plan)")

    sub.add_parser("serve", help="Run persistent WebSocket server daemon inside container (pro plan)")
    sub.add_parser("start-server", help="Start persistent server container (pro plan)")
    sub.add_parser("stop-server", help="Stop persistent server container")

    args = parser.parse_args()

    _DIRECT = {"start-server", "stop-server", "serve"}

    if get_api_plan() == "pro" and not IN_SERVER:
        _require_docker()
        if args.command not in _DIRECT:
            if not _server_is_running():
                print(
                    f"Error: server not running.\n"
                    f"Run: AVE_USE_DOCKER=true API_PLAN=pro AVE_API_KEY=... "
                    f"python scripts/ave_client.py start-server",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.command == "watch-tx":
                _send_to_server(f"subscribe {args.topic} {args.address} {args.chain}")
                return
            if args.command == "watch-kline":
                _send_to_server(f"subscribe kline {args.address} {args.chain} {args.interval}")
                return
            if args.command == "watch-price":
                _send_to_server("subscribe price " + " ".join(args.tokens))
                return
            if args.command == "wss-repl":
                r = subprocess.run(
                    ["docker", "exec", "-it", SERVER_CONTAINER,
                     "python", "scripts/ave_client.py", "wss-repl"],
                )
                sys.exit(r.returncode)
            _exec_in_server(sys.argv[1:])
            return

    commands = {
        "search": cmd_search,
        "token": cmd_token,
        "price": cmd_price,
        "kline-token": cmd_kline_token,
        "kline-pair": cmd_kline_pair,
        "holders": cmd_holders,
        "txs": cmd_txs,
        "platform-tokens": cmd_platform_tokens,
        "trending": cmd_trending,
        "rank-topics": cmd_rank_topics,
        "ranks": cmd_ranks,
        "risk": cmd_risk,
        "chains": cmd_chains,
        "main-tokens": cmd_main_tokens,
        "watch-tx": cmd_watch_tx,
        "watch-kline": cmd_watch_kline,
        "watch-price": cmd_watch_price,
        "wss-repl": cmd_wss_repl,
        "serve": cmd_serve,
        "start-server": cmd_start_server,
        "stop-server": cmd_stop_server,
    }

    try:
        commands[args.command](args)
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
