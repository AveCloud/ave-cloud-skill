"""HTTP facade. Dispatches to sync (urllib) or async (httpx) based on IN_SERVER."""

from __future__ import annotations

import json
import urllib.parse

from ave.config import (
    IN_SERVER, RATE_LIMIT_FILE, TRADE_BASE, TRADE_RATE_LIMIT_FILE, V2_BASE,
)
from ave.headers import data_headers, trade_chain_headers, trade_proxy_headers
from ave.types import Response


async def api_get(path: str, params: dict | None = None) -> Response:
    url = f"{V2_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return await _get(url, data_headers(), RATE_LIMIT_FILE)


async def api_post(path: str, payload: dict) -> Response:
    return await _post(f"{V2_BASE}{path}", payload, data_headers(), RATE_LIMIT_FILE)


async def trade_get(path: str, params: dict | None = None, proxy: bool = False) -> Response:
    url = f"{TRADE_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = trade_proxy_headers("GET", path) if proxy else trade_chain_headers()
    return await _get(url, headers, TRADE_RATE_LIMIT_FILE)


async def trade_post(path: str, payload: dict, proxy: bool = False) -> Response:
    headers = trade_proxy_headers("POST", path, payload) if proxy else trade_chain_headers()
    return await _post(f"{TRADE_BASE}{path}", payload, headers, TRADE_RATE_LIMIT_FILE)


async def rpc_call(rpc_url: str, method: str, params: list) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    data = json.dumps(payload).encode()
    import urllib.request
    req = urllib.request.Request(
        rpc_url, data=data, headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        if "error" in body:
            raise RuntimeError(f"RPC error: {body['error']}")
        return body["result"]


async def _get(url: str, headers: dict[str, str], rate_file: str) -> Response:
    if IN_SERVER:
        from ave.http_async import async_get
        return await async_get(url, headers)
    from ave.http_sync import builtin_rate_limit, urllib_get
    builtin_rate_limit(rate_file)
    return urllib_get(url, headers)


async def _post(url: str, payload: dict, headers: dict[str, str], rate_file: str) -> Response:
    if IN_SERVER:
        from ave.http_async import async_post
        return await async_post(url, payload, headers)
    from ave.http_sync import builtin_rate_limit, urllib_post
    builtin_rate_limit(rate_file)
    return urllib_post(url, payload, headers)
