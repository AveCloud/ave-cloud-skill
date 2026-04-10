#!/usr/bin/env python3
"""AVE Cloud Trade REST API client CLI."""

import asyncio
import sys


def main() -> None:
    from ave.config import IN_SERVER
    from ave.docker import docker_gate
    if not IN_SERVER:
        docker_gate("ave_trade_rest.py")

    import argparse
    from ave.trade.parsers import TRADE_COMMANDS, register_trade_parsers

    parser = argparse.ArgumentParser(description="AVE Cloud Trade REST API client")
    sub = parser.add_subparsers(dest="command", required=True)
    register_trade_parsers(sub)
    args = parser.parse_args()

    try:
        asyncio.run(TRADE_COMMANDS[args.command](args))
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
