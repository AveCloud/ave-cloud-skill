"""Token search commands."""

import argparse
import sys

from ave.http import api_get, api_post
from ave.output import handle_response


async def cmd_search(args: argparse.Namespace) -> None:
    params: dict = {"keyword": args.keyword, "limit": args.limit}
    if args.chain:
        params["chain"] = args.chain
    if args.orderby:
        params["orderby"] = args.orderby
    handle_response(await api_get("/tokens", params))


async def cmd_search_details(args: argparse.Namespace) -> None:
    if len(args.tokens) > 50:
        print("Error: max 50 tokens per request", file=sys.stderr)
        sys.exit(1)
    handle_response(await api_post("/tokens/search", {"token_ids": args.tokens}))


async def cmd_platform_tokens(args: argparse.Namespace) -> None:
    params: dict = {"tag": args.platform}
    if args.limit:
        params["limit"] = args.limit
    if args.orderby:
        params["orderby"] = args.orderby
    handle_response(await api_get("/tokens/platform", params))
