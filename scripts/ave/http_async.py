"""Async HTTP client with asyncio-based rate limiting. Requires httpx."""

from __future__ import annotations

import asyncio
import time

import httpx

from ave.config import PLAN_RPS, get_api_plan
from ave.types import Response


class AsyncRateLimiter:
    def __init__(self, rps: int) -> None:
        self._semaphore = asyncio.Semaphore(1)
        self._interval = 1.0 / rps
        self._last = 0.0

    async def acquire(self) -> None:
        async with self._semaphore:
            wait = self._interval - (time.monotonic() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


_client: httpx.AsyncClient | None = None
_limiter: AsyncRateLimiter | None = None


def _ensure_client() -> tuple[httpx.AsyncClient, AsyncRateLimiter]:
    global _client, _limiter
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
        _limiter = AsyncRateLimiter(PLAN_RPS[get_api_plan()])
    return _client, _limiter


async def async_get(url: str, headers: dict[str, str]) -> Response:
    client, limiter = _ensure_client()
    await limiter.acquire()
    resp = await client.get(url, headers=headers)
    return Response(resp.status_code, resp.text)


async def async_post(url: str, payload: dict, headers: dict[str, str]) -> Response:
    client, limiter = _ensure_client()
    await limiter.acquire()
    resp = await client.post(url, json=payload, headers=headers)
    return Response(resp.status_code, resp.text)
