"""Response handling and JSON output."""

import json

from ave.types import Response


def handle_response(resp: Response) -> None:
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    print(json.dumps(resp.json(), indent=2))


def response_ok(resp_json: dict) -> bool:
    status = resp_json.get("status")
    return status is None or status in (0, 1, 200)
