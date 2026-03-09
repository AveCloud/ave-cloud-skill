#!/usr/bin/env python3
"""AVE Cloud Data WebSocket API client CLI.

Usage: python ave_data_wss.py <command> [options]
Requires: AVE_API_KEY and API_PLAN=pro environment variables
"""

import argparse
import json
import math
import os
import shlex
import subprocess
import sys
import threading
from collections import deque

_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from ave_data_rest import (
    get_api_key, get_api_plan, USE_DOCKER, IN_SERVER, SERVER_CONTAINER,
    SERVER_FIFO, WSS_BASE, VALID_WSS_INTERVALS, _ensure_docker_image, _server_is_running,
)


def _require_pro():
    if get_api_plan() != "pro":
        print("Error: WebSocket subscriptions require API_PLAN=pro.", file=sys.stderr)
        sys.exit(1)


def _require_docker():
    if not USE_DOCKER:
        print("Error: API_PLAN=pro requires AVE_USE_DOCKER=true.", file=sys.stderr)
        sys.exit(1)


def _send_to_server(line):
    result = subprocess.run(
        ["docker", "exec", SERVER_CONTAINER, "sh", "-c",
         f"echo {shlex.quote(line)} > {SERVER_FIFO}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error sending to server: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Sent. Watch events: docker logs -f {SERVER_CONTAINER}", file=sys.stderr)


def _exec_in_server(args_list):
    cmd = ["docker", "exec"]
    if sys.stdin.isatty() and sys.stdout.isatty():
        cmd.append("-it")
    cmd.extend([SERVER_CONTAINER, "python", "scripts/ave_data_wss.py", *args_list])
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def _exec_in_ephemeral_container(args_list):
    _ensure_docker_image()
    cmd = ["docker", "run", "--rm"]
    if sys.stdin.isatty():
        cmd.append("-i")
    if sys.stdin.isatty() and sys.stdout.isatty():
        cmd.append("-t")
    cmd.extend([
        "-e", "AVE_API_KEY",
        "-e", "API_PLAN",
        "-e", "AVE_USE_DOCKER=true",
        "-e", "AVE_IN_SERVER=true",
        "ave-cloud",
        "python",
        "scripts/ave_data_wss.py",
        *args_list,
    ])
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def _interval_label(interval):
    if interval == "s1":
        return "1s"
    if interval.startswith("k"):
        minutes = int(interval[1:])
        if minutes == 1440:
            return "1d"
        if minutes == 10080:
            return "1w"
        if minutes % 60 == 0:
            return f"{minutes // 60}h"
        return f"{minutes}m"
    return interval


def _format_small_number(value):
    if value is None:
        return "n/a"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == 0:
        return "0"
    abs_number = abs(number)
    if abs_number >= 1:
        return f"{number:,.6f}".rstrip("0").rstrip(".")
    if abs_number >= 0.001:
        return f"{number:.8f}".rstrip("0").rstrip(".")
    raw = f"{abs_number:.12f}".split(".")[1]
    zero_count = 0
    for ch in raw:
        if ch == "0":
            zero_count += 1
        else:
            break
    significant = raw[zero_count:zero_count + 4] or "0"
    prefix = "-" if number < 0 else ""
    return f"{prefix}0.0{{{zero_count}}}{significant}"


def _format_usd(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"
    if abs_number >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"
    if abs_number >= 1_000:
        return f"${number / 1_000:.2f}K"
    return f"${number:.2f}"


def _extract_kline_event(message):
    try:
        body = json.loads(message)
    except json.JSONDecodeError:
        return None
    if not isinstance(body, dict):
        return None
    if body.get("type") == "kline":
        return body
    params = body.get("params")
    if isinstance(params, dict) and params.get("type") == "kline":
        return params
    result = body.get("result")
    if isinstance(result, dict) and result.get("type") == "kline":
        return result
    if isinstance(result, dict) and result.get("topic") == "kline" and isinstance(result.get("kline"), dict):
        source = result["kline"].get("usd") or result["kline"].get("eth")
        if isinstance(source, dict):
            pair_id = result.get("id", "pair")
            chain = "?"
            pair = pair_id
            if isinstance(pair_id, str) and "-" in pair_id:
                pair, chain = pair_id.rsplit("-", 1)
            return {
                "type": "kline",
                "pair": pair,
                "chain": chain,
                "interval": result.get("interval"),
                "time": source.get("time"),
                "open": source.get("open"),
                "high": source.get("high"),
                "low": source.get("low"),
                "close": source.get("close"),
                "volume": source.get("volume"),
            }
    data = body.get("data")
    if isinstance(data, dict) and data.get("type") == "kline":
        return data
    return None


def _sparkline_rows(values, rows=5, width=20):
    clean = []
    for value in values:
        try:
            clean.append(float(value))
        except (TypeError, ValueError):
            continue
    if not clean:
        return []
    if len(clean) > width:
        clean = clean[-width:]
    low = min(clean)
    high = max(clean)
    if math.isclose(high, low):
        label = _format_small_number(high)
        return [f"{label:>12} | {'─' * len(clean)}"]

    levels = [high - (high - low) * idx / (rows - 1) for idx in range(rows)]
    chars = []
    for level in levels:
        row = []
        for value in clean:
            if value >= level:
                row.append("█")
            else:
                row.append(" ")
        chars.append(f"{_format_small_number(level):>12} | {''.join(row).rstrip()}")
    return chars


class _KlineFormatter:
    def __init__(self, history=20):
        self.closes = deque(maxlen=history)

    def render(self, event):
        close = event.get("close")
        self.closes.append(close)
        open_value = event.get("open")
        high = event.get("high")
        low = event.get("low")
        volume = event.get("volume")
        pair = event.get("pair", "pair")
        chain = event.get("chain", "?")
        interval = _interval_label(event.get("interval", "?"))

        pct = None
        try:
            open_float = float(open_value)
            close_float = float(close)
            if open_float:
                pct = (close_float - open_float) / open_float * 100
        except (TypeError, ValueError, ZeroDivisionError):
            pct = None

        direction = "flat"
        if pct is not None:
            if pct > 0:
                direction = "up candle"
            elif pct < 0:
                direction = "down candle"

        lines = [
            f"[{chain}] {pair} {interval}",
            (
                f"O: {_format_small_number(open_value)}  "
                f"H: {_format_small_number(high)}  "
                f"L: {_format_small_number(low)}  "
                f"C: {_format_small_number(close)}"
            ),
        ]
        if pct is not None:
            lines.append(f"Move: {pct:+.2f}%   Vol: {_format_usd(volume)}   Trend: {direction}")
        else:
            lines.append(f"Vol: {_format_usd(volume)}   Trend: {direction}")
        lines.append("")
        lines.extend(_sparkline_rows(self.closes))
        return "\n".join(lines)


def _wss_on_message(ws, message):
    try:
        print(json.dumps(json.loads(message), indent=2), flush=True)
        print("---", flush=True)
    except json.JSONDecodeError:
        print(message, flush=True)


def _wss_connect(on_open, on_message=None):
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
        on_message=on_message or _wss_on_message,
        on_error=on_error,
        on_close=on_close,
    )
    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except KeyboardInterrupt:
        ws.close()


def cmd_watch_tx(args):
    def on_open(ws):
        ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": [args.topic, args.address, args.chain], "id": 1,
        }))
        print(
            f"Connected. Subscribed to {args.topic} for {args.address} on {args.chain}. "
            "Waiting for events...",
            file=sys.stderr,
        )
    _wss_connect(on_open)


def cmd_watch_kline(args):
    on_message = None
    if args.format == "markdown":
        formatter = _KlineFormatter(history=args.history)

        def on_message(ws, message):
            event = _extract_kline_event(message)
            if event is None:
                _wss_on_message(ws, message)
                return
            print(formatter.render(event), flush=True)
            print("---", flush=True)

    def on_open(ws):
        ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": ["kline", args.address, args.interval, args.chain], "id": 1,
        }))
        print(
            f"Connected. Subscribed to kline for {args.address} on {args.chain} "
            f"({args.interval}). Waiting for events...",
            file=sys.stderr,
        )
    _wss_connect(on_open, on_message=on_message)


def cmd_watch_price(args):
    def on_open(ws):
        ws.send(json.dumps({
            "jsonrpc": "2.0", "method": "subscribe",
            "params": ["price", args.tokens], "id": 1,
        }))
        print(
            f"Connected. Subscribed to price for {len(args.tokens)} token(s). Waiting for events...",
            file=sys.stderr,
        )
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
    parser = argparse.ArgumentParser(description="AVE Cloud Data WebSocket API client")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("watch-tx", help="Stream live swap/liquidity events (pro plan)")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--topic", default="tx", choices=["tx", "multi_tx", "liq"])

    p = sub.add_parser("watch-kline", help="Stream live kline updates for a pair (pro plan)")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", default="k60", choices=list(VALID_WSS_INTERVALS))
    p.add_argument("--format", default="raw", choices=["raw", "markdown"])
    p.add_argument("--history", type=int, default=20,
                   help="Number of closes to keep in the markdown mini-chart")

    p = sub.add_parser("watch-price", help="Stream live price changes for tokens (pro plan)")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN")

    sub.add_parser("wss-repl", help="Interactive WebSocket REPL (pro plan)")
    sub.add_parser("serve", help="Run persistent WebSocket server daemon inside container (pro plan)")
    sub.add_parser("start-server", help="Start persistent server container (pro plan)")
    sub.add_parser("stop-server", help="Stop persistent server container")

    args = parser.parse_args()

    _DIRECT = {"start-server", "stop-server", "serve"}

    if get_api_plan() == "pro" and not IN_SERVER:
        _require_docker()
        if args.command not in _DIRECT:
            if args.command == "watch-kline" and args.format != "raw":
                if _server_is_running():
                    _exec_in_server([
                        "watch-kline",
                        "--address", args.address,
                        "--chain", args.chain,
                        "--interval", args.interval,
                        "--format", args.format,
                        "--history", str(args.history),
                    ])
                _exec_in_ephemeral_container([
                    "watch-kline",
                    "--address", args.address,
                    "--chain", args.chain,
                    "--interval", args.interval,
                    "--format", args.format,
                    "--history", str(args.history),
                ])
            if not _server_is_running():
                print(
                    "Error: server not running.\n"
                    "Run: AVE_USE_DOCKER=true API_PLAN=pro AVE_API_KEY=... "
                    "python scripts/ave_data_wss.py start-server",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.command == "watch-tx":
                _send_to_server(f"subscribe {args.topic} {args.address} {args.chain}")
                return
            if args.command == "watch-kline":
                if args.format == "raw":
                    _send_to_server(f"subscribe kline {args.address} {args.chain} {args.interval}")
                    return
                _exec_in_server([
                    "watch-kline",
                    "--address", args.address,
                    "--chain", args.chain,
                    "--interval", args.interval,
                    "--format", args.format,
                    "--history", str(args.history),
                ])
            if args.command == "watch-price":
                _send_to_server("subscribe price " + " ".join(args.tokens))
                return
            if args.command == "wss-repl":
                r = subprocess.run(
                    ["docker", "exec", "-it", SERVER_CONTAINER,
                     "python", "scripts/ave_data_wss.py", "wss-repl"],
                )
                sys.exit(r.returncode)

    commands = {
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
