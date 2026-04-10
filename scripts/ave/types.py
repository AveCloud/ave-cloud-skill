"""Shared response type for sync and async HTTP clients."""

import json
from dataclasses import dataclass


@dataclass
class Response:
    status_code: int
    body: str

    @property
    def text(self) -> str:
        return self.body

    def json(self) -> dict:
        return json.loads(self.body)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}: {self.body}")
