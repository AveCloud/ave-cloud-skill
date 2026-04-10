"""Argparse definitions and command registry for trade REST commands."""

from ave.config import ALL_CHAINS, EVM_CHAINS
from ave.trade.chain import (
    cmd_quote, cmd_auto_slippage, cmd_gas_tip, cmd_approve_chain,
    cmd_create_evm_tx, cmd_send_evm_tx,
    cmd_create_solana_tx, cmd_send_solana_tx, cmd_swap_evm, cmd_swap_solana,
)
from ave.trade.proxy import (
    cmd_list_wallets, cmd_create_wallet, cmd_delete_wallet,
    cmd_market_order, cmd_limit_order, cmd_get_swap_orders, cmd_get_limit_orders,
    cmd_cancel_limit_order, cmd_approve_token, cmd_get_approval, cmd_transfer, cmd_get_transfer,
)

TRADE_COMMANDS = {
    "quote": cmd_quote, "auto-slippage": cmd_auto_slippage, "gas-tip": cmd_gas_tip,
    "approve-chain": cmd_approve_chain,
    "create-evm-tx": cmd_create_evm_tx, "send-evm-tx": cmd_send_evm_tx,
    "create-solana-tx": cmd_create_solana_tx, "send-solana-tx": cmd_send_solana_tx,
    "swap-evm": cmd_swap_evm, "swap-solana": cmd_swap_solana,
    "list-wallets": cmd_list_wallets, "create-wallet": cmd_create_wallet, "delete-wallet": cmd_delete_wallet,
    "market-order": cmd_market_order, "limit-order": cmd_limit_order,
    "get-swap-orders": cmd_get_swap_orders, "get-limit-orders": cmd_get_limit_orders,
    "cancel-limit-order": cmd_cancel_limit_order, "approve-token": cmd_approve_token,
    "get-approval": cmd_get_approval, "transfer": cmd_transfer, "get-transfer": cmd_get_transfer,
}


def register_trade_parsers(sub) -> None:
    p = sub.add_parser("quote", help="Get swap quote (estimated output)")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])

    p = sub.add_parser("auto-slippage", help="Query recommended slippage for a token")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--token", required=True, help="Token address")
    p.add_argument("--use-mev", action="store_true")

    sub.add_parser("gas-tip", help="Query recommended gas prices per chain")

    p = sub.add_parser("approve-chain", help="Approve ERC-20 token for chain wallet swap router")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--token", required=True, help="ERC-20 token address to approve")
    p.add_argument("--in-amount", default=None, help="Amount for quote to discover spender (default: 1e18)")
    p.add_argument("--rpc-url", default=None, help="EVM JSON-RPC URL (overrides env)")

    p = sub.add_parser("create-evm-tx", help="Create unsigned EVM swap transaction")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--creator-address", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")

    p = sub.add_parser("send-evm-tx", help="Submit signed EVM transaction")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--request-tx-id", required=True)
    p.add_argument("--signed-tx", required=True)
    p.add_argument("--use-mev", action="store_true")

    p = sub.add_parser("create-solana-tx", help="Create unsigned Solana swap transaction")
    p.add_argument("--creator-address", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee", required=True)
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")

    p = sub.add_parser("send-solana-tx", help="Submit signed Solana transaction")
    p.add_argument("--request-tx-id", required=True)
    p.add_argument("--signed-tx", required=True)
    p.add_argument("--use-mev", action="store_true")

    p = sub.add_parser("swap-evm", help="One-step EVM swap: create + sign + send (requires key/mnemonic)")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--rpc-url", default=None, help="Required EVM JSON-RPC URL for local signing metadata")

    p = sub.add_parser("swap-solana", help="One-step Solana swap: create + sign + send (requires key/mnemonic)")
    p.add_argument("--in-amount", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--fee", required=True)
    p.add_argument("--fee-recipient", default=None)
    p.add_argument("--fee-recipient-rate", default=None, help="Rebate fee ratio in bps, max 10%% (e.g., 100 = 1%%)")
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--use-mev", action="store_true")

    p = sub.add_parser("list-wallets", help="List proxy wallets")
    p.add_argument("--assets-ids", default=None, help="Comma-separated asset IDs to filter by")

    p = sub.add_parser("create-wallet", help="Create a delegate proxy wallet")
    p.add_argument("--name", required=True)
    p.add_argument("--return-mnemonic", action="store_true")

    p = sub.add_parser("delete-wallet", help="Delete delegate proxy wallets")
    p.add_argument("--assets-ids", required=True, nargs="+")

    p = sub.add_parser("market-order", help="Place a market swap order")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--gas", default=None)
    p.add_argument("--extra-gas", default=None)
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--auto-gas", default=None, choices=["low", "average", "high"])
    p.add_argument("--auto-sell", action="append", default=None, metavar="JSON",
                   help='Auto-sell rule as JSON (repeatable, max 10 default + 1 trailing)')

    p = sub.add_parser("limit-order", help="Place a limit order")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--in-token", required=True)
    p.add_argument("--out-token", required=True)
    p.add_argument("--in-amount", required=True)
    p.add_argument("--swap-type", required=True, choices=["buy", "sell"])
    p.add_argument("--slippage", required=True)
    p.add_argument("--use-mev", action="store_true")
    p.add_argument("--limit-price", required=True)
    p.add_argument("--gas", default=None)
    p.add_argument("--extra-gas", default=None)
    p.add_argument("--expire-time", default=None)
    p.add_argument("--auto-slippage", action="store_true")
    p.add_argument("--auto-gas", default=None, choices=["low", "average", "high"])

    p = sub.add_parser("get-swap-orders", help="Query market swap orders by IDs")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--ids", required=True, help="Comma-separated order IDs")

    p = sub.add_parser("get-limit-orders", help="Query limit orders (paginated)")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--page-size", required=True)
    p.add_argument("--page-no", required=True)
    p.add_argument("--status", default=None, choices=["waiting", "confirmed", "error", "auto_cancelled", "cancelled"])
    p.add_argument("--token", default=None)

    p = sub.add_parser("cancel-limit-order", help="Cancel pending limit orders")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--ids", required=True, nargs="+")

    p = sub.add_parser("approve-token", help="Approve token for EVM proxy wallet trading")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--token-address", required=True)

    p = sub.add_parser("get-approval", help="Query token approval status")
    p.add_argument("--chain", required=True, choices=EVM_CHAINS)
    p.add_argument("--ids", required=True, help="Comma-separated approval order IDs")

    p = sub.add_parser("transfer", help="Transfer tokens from a delegate proxy wallet")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--assets-id", required=True)
    p.add_argument("--from-address", required=True)
    p.add_argument("--to-address", required=True)
    p.add_argument("--token-address", required=True)
    p.add_argument("--amount", required=True)
    p.add_argument("--gas", default=None)
    p.add_argument("--extra-gas", default=None)

    p = sub.add_parser("get-transfer", help="Query transfer status")
    p.add_argument("--chain", required=True, choices=ALL_CHAINS)
    p.add_argument("--ids", required=True, help="Comma-separated transfer order IDs")
