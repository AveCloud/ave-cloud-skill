"""Market info, rankings, risk, and chain commands."""

import argparse

from ave.http import api_get
from ave.output import handle_response


async def cmd_trending(args: argparse.Namespace) -> None:
    params = {"chain": args.chain, "current_page": args.page, "page_size": args.page_size}
    handle_response(await api_get("/tokens/trending", params))


async def cmd_rank_topics(args: argparse.Namespace) -> None:
    handle_response(await api_get("/ranks/topics"))


async def cmd_ranks(args: argparse.Namespace) -> None:
    handle_response(await api_get("/ranks", {"topic": args.topic}))


async def cmd_risk(args: argparse.Namespace) -> None:
    handle_response(await api_get(f"/contracts/{args.address}-{args.chain}"))


async def cmd_chains(args: argparse.Namespace) -> None:
    handle_response(await api_get("/supported_chains"))


async def cmd_main_tokens(args: argparse.Namespace) -> None:
    handle_response(await api_get("/tokens/main", {"chain": args.chain}))
