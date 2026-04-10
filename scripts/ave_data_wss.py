#!/usr/bin/env python3
"""AVE Cloud Data WebSocket API client CLI."""

import asyncio
import sys


def main() -> None:
    from ave.config import IN_SERVER
    from ave.docker import docker_gate
    if not IN_SERVER:
        docker_gate("ave_data_wss.py")

    import argparse
    from ave.wss.parsers import DATA_WSS_COMMANDS, register_data_wss_parsers

    parser = argparse.ArgumentParser(description="AVE Cloud Data WebSocket API client")
    sub = parser.add_subparsers(dest="command", required=True)
    register_data_wss_parsers(sub)
    args = parser.parse_args()

    try:
        asyncio.run(DATA_WSS_COMMANDS[args.command](args))
    except (EnvironmentError, ValueError, ImportError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
