"""Header builders for data API, trade chain, and trade proxy (HMAC)."""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json

from ave.config import get_api_key, get_secret_key


def data_headers() -> dict[str, str]:
    return {"X-API-KEY": get_api_key(), "Content-Type": "application/json"}


def trade_chain_headers() -> dict[str, str]:
    return {"AVE-ACCESS-KEY": get_api_key(), "Content-Type": "application/json"}


def trade_proxy_headers(method: str, path: str, body: dict | None = None) -> dict[str, str]:
    timestamp, signature = _trade_sign(method, path, body)
    return {
        "AVE-ACCESS-KEY": get_api_key(),
        "AVE-ACCESS-TIMESTAMP": timestamp,
        "AVE-ACCESS-SIGN": signature,
        "Content-Type": "application/json",
    }


def _trade_sign(method: str, path: str, body: dict | None = None) -> tuple[str, str]:
    secret = get_secret_key()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    message = timestamp + method.upper().strip() + path.strip()
    if body:
        message += json.dumps(body, sort_keys=True, separators=(",", ":"))
    h = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
    return timestamp, base64.b64encode(h.digest()).decode()
