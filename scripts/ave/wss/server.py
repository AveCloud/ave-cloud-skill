"""WebSocket server daemon and Docker server management."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys

from ave.config import SERVER_CONTAINER, SERVER_FIFO, WSS_BASE, USE_DOCKER, get_api_key, get_api_plan
from ave.docker import ensure_docker_image, server_is_running


async def cmd_serve(args: argparse.Namespace) -> None:
    if get_api_plan() != "pro":
        print("Error: WebSocket subscriptions require API_PLAN=pro.", file=sys.stderr)
        sys.exit(1)
    if os.path.exists(SERVER_FIFO):
        os.remove(SERVER_FIFO)
    os.mkfifo(SERVER_FIFO)
    import websockets
    headers = {"X-API-KEY": get_api_key()}
    msg_id = 0
    loop = asyncio.get_event_loop()

    async with websockets.connect(WSS_BASE, additional_headers=headers) as ws:
        async def _reader() -> None:
            async for message in ws:
                try:
                    print(json.dumps(json.loads(message), indent=2), flush=True)
                except json.JSONDecodeError:
                    print(message, flush=True)
                print("---", flush=True)

        read_task = asyncio.create_task(_reader())
        print("Server ready.", file=sys.stderr, flush=True)

        def _read_fifo_line() -> str:
            with open(SERVER_FIFO, "r") as pipe:
                for raw in pipe:
                    return raw.strip()
            return ""

        try:
            while True:
                line = await loop.run_in_executor(None, _read_fifo_line)
                if not line:
                    continue
                parts = line.split()
                cmd = parts[0].lower()
                if cmd == "subscribe" and len(parts) >= 2:
                    msg_id += 1
                    topic = parts[1]
                    if topic == "price" and len(parts) >= 3:
                        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": ["price", parts[2:]], "id": msg_id}))
                    elif topic in ("tx", "multi_tx", "liq") and len(parts) >= 4:
                        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": [topic, parts[2], parts[3]], "id": msg_id}))
                    elif topic == "kline" and len(parts) >= 4:
                        iv = parts[4] if len(parts) > 4 else "k60"
                        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "subscribe", "params": ["kline", parts[2], iv, parts[3]], "id": msg_id}))
                    print(f"Subscribed: {' '.join(parts[1:])}", file=sys.stderr, flush=True)
                elif cmd == "unsubscribe":
                    msg_id += 1
                    await ws.send(json.dumps({"jsonrpc": "2.0", "method": "unsubscribe", "params": [], "id": msg_id}))
                    print("Unsubscribed.", file=sys.stderr, flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            read_task.cancel()


async def cmd_start_server(args: argparse.Namespace) -> None:
    if get_api_plan() != "pro":
        print("Error: WebSocket subscriptions require API_PLAN=pro.", file=sys.stderr)
        sys.exit(1)
    if not USE_DOCKER:
        print("Error: API_PLAN=pro requires AVE_USE_DOCKER=true.", file=sys.stderr)
        sys.exit(1)
    if server_is_running():
        print(f"Server already running: {SERVER_CONTAINER}", file=sys.stderr)
        return
    subprocess.run(["docker", "rm", "-f", SERVER_CONTAINER], capture_output=True)
    result = subprocess.run([
        "docker", "run", "-d", "--name", SERVER_CONTAINER,
        "-e", "AVE_API_KEY", "-e", "API_PLAN=pro",
        "-e", "AVE_USE_DOCKER=true", "-e", "AVE_IN_SERVER=true",
        "ave-cloud", "serve",
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Started ({result.stdout.strip()[:12]}). Logs: docker logs -f {SERVER_CONTAINER}", file=sys.stderr)


async def cmd_stop_server(args: argparse.Namespace) -> None:
    result = subprocess.run(["docker", "rm", "-f", SERVER_CONTAINER], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Server stopped: {SERVER_CONTAINER}", file=sys.stderr)
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
