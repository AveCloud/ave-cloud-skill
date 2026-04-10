"""Argparse definitions and command registry for data REST commands."""

from ave.constants import VALID_PLATFORMS
from ave.data.search import cmd_search, cmd_search_details, cmd_platform_tokens
from ave.data.token import cmd_token, cmd_price, cmd_holders
from ave.data.kline import cmd_kline_token, cmd_kline_pair, cmd_kline_ondo
from ave.data.market import cmd_trending, cmd_rank_topics, cmd_ranks, cmd_risk, cmd_chains, cmd_main_tokens
from ave.data.wallet import cmd_address_txs, cmd_address_pnl, cmd_wallet_tokens, cmd_wallet_info, cmd_smart_wallets
from ave.data.tx import cmd_txs, cmd_liq_txs, cmd_tx_detail, cmd_pair, cmd_signals

DATA_COMMANDS = {
    "search": cmd_search, "search-details": cmd_search_details, "platform-tokens": cmd_platform_tokens,
    "token": cmd_token, "price": cmd_price, "holders": cmd_holders,
    "kline-token": cmd_kline_token, "kline-pair": cmd_kline_pair, "kline-ondo": cmd_kline_ondo,
    "trending": cmd_trending, "rank-topics": cmd_rank_topics, "ranks": cmd_ranks,
    "risk": cmd_risk, "chains": cmd_chains, "main-tokens": cmd_main_tokens,
    "address-txs": cmd_address_txs, "address-pnl": cmd_address_pnl,
    "wallet-tokens": cmd_wallet_tokens, "wallet-info": cmd_wallet_info, "smart-wallets": cmd_smart_wallets,
    "txs": cmd_txs, "liq-txs": cmd_liq_txs, "tx-detail": cmd_tx_detail,
    "pair": cmd_pair, "signals": cmd_signals,
}


def register_data_parsers(sub) -> None:
    p = sub.add_parser("search", help="Search tokens by keyword")
    p.add_argument("--keyword", required=True)
    p.add_argument("--chain", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--orderby", default=None, choices=["tx_volume_u_24h", "main_pair_tvl", "fdv", "market_cap"])

    p = sub.add_parser("platform-tokens", help="Get tokens by platform/launchpad tag")
    p.add_argument("--platform", required=True, choices=VALID_PLATFORMS)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--orderby", default=None, choices=["tx_volume_u_24h", "main_pair_tvl"])

    p = sub.add_parser("token", help="Get token detail")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

    p = sub.add_parser("price", help="Get prices for up to 200 tokens")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN")
    p.add_argument("--tvl-min", type=float, default=None)
    p.add_argument("--volume-min", type=float, default=None)

    p = sub.add_parser("kline-token", help="Get kline data by token address")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", type=int, default=60, choices=[1, 5, 15, 30, 60, 120, 240, 1440, 4320, 10080])
    p.add_argument("--size", type=int, default=24)

    p = sub.add_parser("kline-pair", help="Get kline data by pair address")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--interval", type=int, default=60, choices=[1, 5, 15, 30, 60, 120, 240, 1440, 4320, 10080])
    p.add_argument("--size", type=int, default=24)

    p = sub.add_parser("kline-ondo", help="Get Ondo-mapped kline data by pair address or ticker")
    p.add_argument("--pair", required=True, help="pair_address-chain or ticker symbol")
    p.add_argument("--interval", type=int, default=60, choices=[1, 5, 15, 60, 240, 720, 1440])
    p.add_argument("--size", type=int, default=24)
    p.add_argument("--from-time", type=int, default=None)
    p.add_argument("--to-time", type=int, default=None)

    p = sub.add_parser("holders", help="Get token holders with sort/order")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--sort-by", default="balance", choices=["balance", "percentage"])
    p.add_argument("--order", default="desc", choices=["asc", "desc"])

    p = sub.add_parser("search-details", help="Batch search token details by address-chain list")
    p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN", help="Up to 50 address-chain identifiers")

    p = sub.add_parser("txs", help="Get swap transactions for a pair")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

    p = sub.add_parser("trending", help="Get trending tokens on a chain")
    p.add_argument("--chain", required=True)
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--page-size", type=int, default=20)

    sub.add_parser("rank-topics", help="List available rank topics")

    p = sub.add_parser("ranks", help="Get token rankings by topic")
    p.add_argument("--topic", required=True)

    p = sub.add_parser("risk", help="Get contract risk/security report")
    p.add_argument("--address", required=True)
    p.add_argument("--chain", required=True)

    sub.add_parser("chains", help="List all supported chains")

    p = sub.add_parser("main-tokens", help="Get main tokens for a chain")
    p.add_argument("--chain", required=True)

    p = sub.add_parser("address-txs", help="Get wallet swap transaction history")
    p.add_argument("--wallet", required=True, help="Wallet address")
    p.add_argument("--chain", required=True)
    p.add_argument("--token", default=None, help="Filter by token address")
    p.add_argument("--from-time", type=int, default=None, help="Unix timestamp start")
    p.add_argument("--last-time", default=None, help="RFC3339 cursor for pagination")
    p.add_argument("--last-id", default=None, help="Cursor ID for pagination")
    p.add_argument("--page-size", type=int, default=None, help="Results per page (max 100)")

    p = sub.add_parser("address-pnl", help="Get wallet PnL for a specific token")
    p.add_argument("--wallet", required=True, help="Wallet address")
    p.add_argument("--chain", required=True)
    p.add_argument("--token", required=True, help="Token contract address")

    p = sub.add_parser("wallet-tokens", help="Get token holdings for a wallet")
    p.add_argument("--wallet", required=True, help="Wallet address")
    p.add_argument("--chain", required=True)
    p.add_argument("--sort", default=None, help="Sort field (default: last_txn_time)")
    p.add_argument("--sort-dir", default=None, choices=["asc", "desc"])
    p.add_argument("--page-size", type=int, default=None)
    p.add_argument("--page-no", type=int, default=None)
    p.add_argument("--hide-sold", action="store_true", help="Hide tokens with zero balance")
    p.add_argument("--hide-small", type=float, default=None, help="Hide tokens below USD value")
    p.add_argument("--blue-chips", action="store_true", help="Only show blue-chip tokens")

    p = sub.add_parser("wallet-info", help="Get wallet overview and stats")
    p.add_argument("--wallet", required=True, help="Wallet address to inspect")
    p.add_argument("--chain", required=True)
    p.add_argument("--self-address", default=None, help="Your own address for relative stats")

    p = sub.add_parser("smart-wallets", help="List smart wallets with profit filters")
    p.add_argument("--chain", required=True)
    p.add_argument("--keyword", default=None, help="Search by address keyword")
    p.add_argument("--sort", default=None)
    p.add_argument("--sort-dir", default=None, choices=["asc", "desc"])
    p.add_argument("--profit-above-900-percent-num-min", type=float, default=None, dest="profit_above_900_percent_num_min")
    p.add_argument("--profit-above-900-percent-num-max", type=float, default=None, dest="profit_above_900_percent_num_max")
    p.add_argument("--profit-300-900-percent-num-min", type=float, default=None, dest="profit_300_900_percent_num_min")
    p.add_argument("--profit-300-900-percent-num-max", type=float, default=None, dest="profit_300_900_percent_num_max")
    p.add_argument("--profit-100-300-percent-num-min", type=float, default=None, dest="profit_100_300_percent_num_min")
    p.add_argument("--profit-100-300-percent-num-max", type=float, default=None, dest="profit_100_300_percent_num_max")
    p.add_argument("--profit-10-100-percent-num-min", type=float, default=None, dest="profit_10_100_percent_num_min")
    p.add_argument("--profit-10-100-percent-num-max", type=float, default=None, dest="profit_10_100_percent_num_max")
    p.add_argument("--profit-neg10-10-percent-num-min", type=float, default=None, dest="profit_neg10_10_percent_num_min")
    p.add_argument("--profit-neg10-10-percent-num-max", type=float, default=None, dest="profit_neg10_10_percent_num_max")
    p.add_argument("--profit-neg50-neg10-percent-num-min", type=float, default=None, dest="profit_neg50_neg10_percent_num_min")
    p.add_argument("--profit-neg50-neg10-percent-num-max", type=float, default=None, dest="profit_neg50_neg10_percent_num_max")
    p.add_argument("--profit-neg100-neg50-percent-num-min", type=float, default=None, dest="profit_neg100_neg50_percent_num_min")
    p.add_argument("--profit-neg100-neg50-percent-num-max", type=float, default=None, dest="profit_neg100_neg50_percent_num_max")
    p.add_argument("--last-trade-time-min", type=float, default=None, dest="last_trade_time_min")
    p.add_argument("--last-trade-time-max", type=float, default=None, dest="last_trade_time_max")

    p = sub.add_parser("signals", help="Get public trading signals")
    p.add_argument("--chain", default="solana")
    p.add_argument("--page-size", type=int, default=10)
    p.add_argument("--page-no", type=int, default=1)

    p = sub.add_parser("liq-txs", help="Get liquidity transactions for a pair")
    p.add_argument("--address", required=True, help="Pair address")
    p.add_argument("--chain", required=True)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--from-time", type=int, default=None, help="Unix timestamp start")
    p.add_argument("--to-time", type=int, default=None, help="Unix timestamp end")
    p.add_argument("--type", default="all", choices=["addLiquidity", "removeLiquidity", "createPair", "all"])
    p.add_argument("--sort", default="asc", choices=["asc", "desc"])

    p = sub.add_parser("tx-detail", help="Get transaction detail by hash")
    p.add_argument("--chain", required=True)
    p.add_argument("--account", required=True, help="Account address involved in the tx")
    p.add_argument("--tx-hash", required=True, help="Transaction hash")
    p.add_argument("--start-from", type=int, default=None, help="Unix timestamp range start")
    p.add_argument("--end-at", type=int, default=None, help="Unix timestamp range end")
    p.add_argument("--limit", type=int, default=None)

    p = sub.add_parser("pair", help="Get trading pair detail")
    p.add_argument("--address", required=True, help="Pair contract address")
    p.add_argument("--chain", required=True)
