"""Argparse definitions and command registry for WSS commands."""

from ave.constants import VALID_WSS_INTERVALS
from ave.wss.stream import cmd_watch_tx, cmd_watch_kline, cmd_watch_price
from ave.wss.repl import cmd_wss_repl
from ave.wss.server import cmd_serve, cmd_start_server, cmd_stop_server

DATA_WSS_COMMANDS = {
    "watch-tx": cmd_watch_tx, "watch-kline": cmd_watch_kline, "watch-price": cmd_watch_price,
    "wss-repl": cmd_wss_repl, "serve": cmd_serve, "start-server": cmd_start_server, "stop-server": cmd_stop_server,
}


def register_data_wss_parsers(sub) -> None:
    p = sub.add_parser("watch-tx", help="Stream live swap/liquidity events (pro plan)")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--topic", default="tx", choices=["tx", "multi_tx", "liq"])

    p = sub.add_parser("watch-kline", help="Stream live kline updates for a pair (pro plan)")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", default="k60", choices=list(VALID_WSS_INTERVALS))
    p.add_argument("--format", default="raw", choices=["raw", "markdown"])
    p.add_argument("--history", type=int, default=20, help="Closes to keep in mini-chart")

    p = sub.add_parser("watch-price", help="Stream live price changes for tokens (pro plan)")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN")

    sub.add_parser("wss-repl", help="Interactive WebSocket REPL (pro plan)")
    sub.add_parser("serve", help="Run persistent WebSocket server daemon inside container (pro plan)")
    sub.add_parser("start-server", help="Start persistent server container (pro plan)")
    sub.add_parser("stop-server", help="Stop persistent server container")
