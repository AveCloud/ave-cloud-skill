"""Stdlib-only HTTP client with file-lock rate limiting. Zero external deps."""

import fcntl
import json
import time
import urllib.error
import urllib.request

from ave.config import PLAN_MIN_INTERVAL, get_api_plan
from ave.types import Response


def builtin_rate_limit(rate_file: str) -> None:
    min_interval = PLAN_MIN_INTERVAL[get_api_plan()]
    with open(rate_file, "a+") as f:
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


def urllib_get(url: str, headers: dict[str, str]) -> Response:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return Response(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return Response(e.code, body)


def urllib_post(url: str, payload: dict, headers: dict[str, str]) -> Response:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return Response(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return Response(e.code, body)
