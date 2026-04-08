# Data REST API Expansion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 11 new endpoints and replace 1 existing endpoint in `ave_data_rest.py`, then reorganize CLI commands into functional groups in SKILL.md.

**Architecture:** Each new endpoint follows the existing pattern in `ave_data_rest.py`: add a `cmd_*` function calling `api_get`/`api_post`, register an argparse subcommand, wire it into the `commands` dict. The SKILL.md and `data-api-doc.md` get updated to reflect groupings and new commands.

**Tech Stack:** Python 3 (stdlib `urllib` + `argparse`), AVE Cloud Data REST API v2

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `scripts/ave_data_rest.py` | Add 11 commands, replace `holders` endpoint |
| Modify | `skills/data-rest/SKILL.md` | Reorganize into groups, document new commands |
| Modify | `references/data-api-doc.md` | Add reference entries for new endpoints |

## API Parameter Reference

Extracted from Go controllers. Each new command maps to these exact query params.

| Command | Method | Path | Required Params | Optional Params |
|---------|--------|------|-----------------|-----------------|
| `holders` (replace) | GET | `/tokens/holders/{addr}-{chain}` | `--address`, `--chain` | `--limit` (1-100, default 100), `--sort-by` (balance/percentage, default balance), `--order` (asc/desc, default desc) |
| `search-details` | POST | `/tokens/search` | `--tokens` (list of addr-chain) | none (max 50) |
| `kline-ondo` | GET | `/klines/pair/ondo/{id}` | `--pair` (addr-chain or ticker) | `--interval` (1,5,15,60,240,720,1440), `--size`, `--from-time`, `--to-time` |
| `address-txs` | GET | `/address/tx` | `--wallet`, `--chain` | `--token`, `--from-time`, `--last-time`, `--last-id`, `--page-size` (max 100) |
| `address-pnl` | GET | `/address/pnl` | `--wallet`, `--chain`, `--token` | none |
| `wallet-tokens` | GET | `/address/walletinfo/tokens` | `--wallet`, `--chain` | `--sort` (default last_txn_time), `--sort-dir`, `--page-size`, `--page-no`, `--hide-sold`, `--hide-small`, `--blue-chips` |
| `wallet-info` | GET | `/address/walletinfo` | `--wallet`, `--chain` | `--self-address` |
| `smart-wallets` | GET | `/address/smart_wallet/list` | `--chain` | `--keyword`, `--sort`, `--sort-dir`, plus 16 profit-range filter params |
| `signals` | GET | `/signals/public/list` | none | `--chain` (default solana), `--page-size` (max 50), `--page-no` |
| `liq-txs` | GET | `/txs/liq/{pair}-{chain}` | `--address`, `--chain` | `--limit`, `--from-time`, `--to-time`, `--type` (addLiquidity/removeLiquidity/createPair/all), `--sort` |
| `tx-detail` | GET | `/txs/detail` | `--chain`, `--account`, `--tx-hash` | `--start-from`, `--end-at`, `--limit` |
| `pair` | GET | `/pairs/{pair}-{chain}` | `--address`, `--chain` | none |

---

### Task 1: Replace `holders` with `/v2/tokens/holders/{tokenId}`

**Files:**
- Modify: `scripts/ave_data_rest.py:362-367` (cmd_holders function)
- Modify: `scripts/ave_data_rest.py:437-439` (argparse for holders)

- [ ] **Step 1: Update `cmd_holders` to call the new endpoint with sort params**

In `scripts/ave_data_rest.py`, replace the existing `cmd_holders` function:

```python
def cmd_holders(args):
    params = {}
    if args.limit:
        params["limit"] = args.limit
    if args.sort_by:
        params["sort_by"] = args.sort_by
    if args.order:
        params["order"] = args.order
    handle_response(api_get(f"/tokens/holders/{args.address}-{args.chain}", params))
```

- [ ] **Step 2: Update the argparse block for `holders`**

Replace the existing `holders` subparser:

```python
p = sub.add_parser("holders", help="Get token holders with sort/order")
p.add_argument("--address", required=True)
p.add_argument("--chain", required=True)
p.add_argument("--limit", type=int, default=100)
p.add_argument("--sort-by", default="balance", choices=["balance", "percentage"])
p.add_argument("--order", default="desc", choices=["asc", "desc"])
```

- [ ] **Step 3: Test manually**

Run: `python scripts/ave_data_rest.py holders --address 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c --chain bsc --limit 10`

Expected: JSON with `status: 1` and holder data array.

- [ ] **Step 4: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): replace holders endpoint with /v2/tokens/holders"
```

---

### Task 2: Add `search-details` command (POST /v2/tokens/search)

**Files:**
- Modify: `scripts/ave_data_rest.py` (add cmd function + argparse + commands entry)

- [ ] **Step 1: Add the command function**

Add after `cmd_holders`:

```python
def cmd_search_details(args):
    if len(args.tokens) > 50:
        print("Error: max 50 tokens per request", file=sys.stderr)
        sys.exit(1)
    payload = {"token_ids": args.tokens}
    handle_response(api_post("/tokens/search", payload))
```

- [ ] **Step 2: Add argparse subcommand**

Add after the `holders` parser block:

```python
p = sub.add_parser("search-details", help="Batch search token details by address-chain list")
p.add_argument("--tokens", required=True, nargs="+", metavar="ADDRESS-CHAIN",
               help="Up to 50 address-chain identifiers")
```

- [ ] **Step 3: Wire into commands dict**

Add to the `commands` dict:

```python
"search-details": cmd_search_details,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py search-details --tokens 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c-bsc`

Expected: JSON with token detail array.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add search-details command for batch token lookup"
```

---

### Task 3: Add `kline-ondo` command (GET /v2/klines/pair/ondo/{pairId})

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

Add after `cmd_kline_pair`:

```python
def cmd_kline_ondo(args):
    params = {"interval": args.interval, "limit": args.size}
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.to_time is not None:
        params["to_time"] = args.to_time
    resp = api_get(f"/klines/pair/ondo/{args.pair}", params)
    if resp.status_code >= 400:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    body = resp.json()
    points = body.get("data", {}).get("points")
    if isinstance(points, list) and len(points) > args.size:
        body["data"]["points"] = points[-args.size:]
        body["data"]["limit"] = args.size
        body["data"]["total_count"] = len(body["data"]["points"])
    print(json.dumps(body, indent=2))
```

- [ ] **Step 2: Add argparse subcommand**

Add after the `kline-pair` parser block:

```python
p = sub.add_parser("kline-ondo", help="Get Ondo-mapped kline data by pair address or ticker")
p.add_argument("--pair", required=True, help="pair_address-chain or ticker symbol")
p.add_argument("--interval", type=int, default=60, choices=[1, 5, 15, 60, 240, 720, 1440])
p.add_argument("--size", type=int, default=24)
p.add_argument("--from-time", type=int, default=None)
p.add_argument("--to-time", type=int, default=None)
```

- [ ] **Step 3: Wire into commands dict**

```python
"kline-ondo": cmd_kline_ondo,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py kline-ondo --pair BTC-USD --interval 60 --size 10`

Expected: JSON with kline points array or "pair not found" success message.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add kline-ondo command for Ondo-mapped klines"
```

---

### Task 4: Add `address-txs` command (GET /v2/address/tx)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_address_txs(args):
    params = {"wallet_address": args.wallet, "chain": args.chain}
    if args.token:
        params["token_address"] = args.token
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.last_time:
        params["last_time"] = args.last_time
    if args.last_id:
        params["last_id"] = args.last_id
    if args.page_size:
        params["page_size"] = args.page_size
    handle_response(api_get("/address/tx", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("address-txs", help="Get wallet swap transaction history")
p.add_argument("--wallet", required=True, help="Wallet address")
p.add_argument("--chain", required=True)
p.add_argument("--token", default=None, help="Filter by token address")
p.add_argument("--from-time", type=int, default=None, help="Unix timestamp start")
p.add_argument("--last-time", default=None, help="RFC3339 cursor for pagination")
p.add_argument("--last-id", default=None, help="Cursor ID for pagination")
p.add_argument("--page-size", type=int, default=None, help="Results per page (max 100)")
```

- [ ] **Step 3: Wire into commands dict**

```python
"address-txs": cmd_address_txs,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py address-txs --wallet 0x... --chain bsc`

Expected: JSON with swap tx list and pagination cursors.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add address-txs command for wallet swap history"
```

---

### Task 5: Add `address-pnl` command (GET /v2/address/pnl)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_address_pnl(args):
    params = {
        "wallet_address": args.wallet,
        "chain": args.chain,
        "token_address": args.token,
    }
    handle_response(api_get("/address/pnl", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("address-pnl", help="Get wallet PnL for a specific token")
p.add_argument("--wallet", required=True, help="Wallet address")
p.add_argument("--chain", required=True)
p.add_argument("--token", required=True, help="Token contract address")
```

- [ ] **Step 3: Wire into commands dict**

```python
"address-pnl": cmd_address_pnl,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py address-pnl --wallet 0x... --chain bsc --token 0x...`

Expected: JSON with PnL data.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add address-pnl command for wallet token PnL"
```

---

### Task 6: Add `wallet-tokens` command (GET /v2/address/walletinfo/tokens)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_wallet_tokens(args):
    params = {"wallet_address": args.wallet, "chain": args.chain}
    if args.sort:
        params["sort"] = args.sort
    if args.sort_dir:
        params["sort_dir"] = args.sort_dir
    if args.page_size:
        params["pageSize"] = args.page_size
    if args.page_no:
        params["pageNO"] = args.page_no
    if args.hide_sold:
        params["hide_sold"] = 1
    if args.hide_small is not None:
        params["hide_small"] = args.hide_small
    if args.blue_chips:
        params["blue_chips"] = 1
    handle_response(api_get("/address/walletinfo/tokens", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
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
```

- [ ] **Step 3: Wire into commands dict**

```python
"wallet-tokens": cmd_wallet_tokens,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py wallet-tokens --wallet 0x... --chain bsc`

Expected: JSON with paginated token holdings.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add wallet-tokens command for wallet holdings"
```

---

### Task 7: Add `wallet-info` command (GET /v2/address/walletinfo)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_wallet_info(args):
    params = {"wallet_address": args.wallet, "chain": args.chain}
    if args.self_address:
        params["self_address"] = args.self_address
    handle_response(api_get("/address/walletinfo", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("wallet-info", help="Get wallet overview and stats")
p.add_argument("--wallet", required=True, help="Wallet address to inspect")
p.add_argument("--chain", required=True)
p.add_argument("--self-address", default=None, help="Your own address for relative stats")
```

- [ ] **Step 3: Wire into commands dict**

```python
"wallet-info": cmd_wallet_info,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py wallet-info --wallet 0x... --chain bsc`

Expected: JSON with wallet overview.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add wallet-info command for wallet overview"
```

---

### Task 8: Add `smart-wallets` command (GET /v2/address/smart_wallet/list)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_smart_wallets(args):
    params = {"chain": args.chain}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.sort:
        params["sort"] = args.sort
    if args.sort_dir:
        params["sort_dir"] = args.sort_dir
    for name in (
        "profit_above_900_percent_num_min", "profit_above_900_percent_num_max",
        "profit_300_900_percent_num_min", "profit_300_900_percent_num_max",
        "profit_100_300_percent_num_min", "profit_100_300_percent_num_max",
        "profit_10_100_percent_num_min", "profit_10_100_percent_num_max",
        "profit_neg10_10_percent_num_min", "profit_neg10_10_percent_num_max",
        "profit_neg50_neg10_percent_num_min", "profit_neg50_neg10_percent_num_max",
        "profit_neg100_neg50_percent_num_min", "profit_neg100_neg50_percent_num_max",
        "last_trade_time_min", "last_trade_time_max",
    ):
        val = getattr(args, name, None)
        if val is not None:
            params[name] = val
    handle_response(api_get("/address/smart_wallet/list", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
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
```

- [ ] **Step 3: Wire into commands dict**

```python
"smart-wallets": cmd_smart_wallets,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py smart-wallets --chain solana`

Expected: JSON with smart wallet list.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add smart-wallets command for smart wallet discovery"
```

---

### Task 9: Add `signals` command (GET /v2/signals/public/list)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_signals(args):
    params = {"chain": args.chain, "pageSize": args.page_size, "pageNO": args.page_no}
    handle_response(api_get("/signals/public/list", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("signals", help="Get public trading signals")
p.add_argument("--chain", default="solana")
p.add_argument("--page-size", type=int, default=10)
p.add_argument("--page-no", type=int, default=1)
```

- [ ] **Step 3: Wire into commands dict**

```python
"signals": cmd_signals,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py signals --chain solana`

Expected: JSON with signal list.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add signals command for public trading signals"
```

---

### Task 10: Add `liq-txs` command (GET /v2/txs/liq/{pairId})

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
VALID_LIQ_TYPES = ("addLiquidity", "removeLiquidity", "createPair", "all")

def cmd_liq_txs(args):
    params = {"limit": args.limit, "sort": args.sort}
    if args.from_time is not None:
        params["from_time"] = args.from_time
    if args.to_time is not None:
        params["to_time"] = args.to_time
    if args.type:
        params["type"] = args.type
    handle_response(api_get(f"/txs/liq/{args.address}-{args.chain}", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("liq-txs", help="Get liquidity transactions for a pair")
p.add_argument("--address", required=True, help="Pair address")
p.add_argument("--chain", required=True)
p.add_argument("--limit", type=int, default=100)
p.add_argument("--from-time", type=int, default=None, help="Unix timestamp start")
p.add_argument("--to-time", type=int, default=None, help="Unix timestamp end")
p.add_argument("--type", default="all",
               choices=["addLiquidity", "removeLiquidity", "createPair", "all"])
p.add_argument("--sort", default="asc", choices=["asc", "desc"])
```

- [ ] **Step 3: Wire into commands dict**

```python
"liq-txs": cmd_liq_txs,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py liq-txs --address 0x... --chain bsc --limit 5`

Expected: JSON with liquidity tx list.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add liq-txs command for liquidity transactions"
```

---

### Task 11: Add `tx-detail` command (GET /v2/txs/detail)

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_tx_detail(args):
    params = {
        "chain": args.chain,
        "account_address": args.account,
        "tx_hash": args.tx_hash,
    }
    if args.start_from is not None:
        params["start_from"] = args.start_from
    if args.end_at is not None:
        params["end_at"] = args.end_at
    if args.limit:
        params["limit"] = args.limit
    handle_response(api_get("/txs/detail", params))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("tx-detail", help="Get transaction detail by hash")
p.add_argument("--chain", required=True)
p.add_argument("--account", required=True, help="Account address involved in the tx")
p.add_argument("--tx-hash", required=True, help="Transaction hash")
p.add_argument("--start-from", type=int, default=None, help="Unix timestamp range start")
p.add_argument("--end-at", type=int, default=None, help="Unix timestamp range end")
p.add_argument("--limit", type=int, default=None)
```

- [ ] **Step 3: Wire into commands dict**

```python
"tx-detail": cmd_tx_detail,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py tx-detail --chain bsc --account 0x... --tx-hash 0x...`

Expected: JSON with tx detail.

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add tx-detail command for transaction lookup"
```

---

### Task 12: Add `pair` command (GET /v2/pairs/{pairId})

**Files:**
- Modify: `scripts/ave_data_rest.py`

- [ ] **Step 1: Add the command function**

```python
def cmd_pair(args):
    handle_response(api_get(f"/pairs/{args.address}-{args.chain}"))
```

- [ ] **Step 2: Add argparse subcommand**

```python
p = sub.add_parser("pair", help="Get trading pair detail")
p.add_argument("--address", required=True, help="Pair contract address")
p.add_argument("--chain", required=True)
```

- [ ] **Step 3: Wire into commands dict**

```python
"pair": cmd_pair,
```

- [ ] **Step 4: Test manually**

Run: `python scripts/ave_data_rest.py pair --address 0x... --chain bsc`

Expected: JSON with pair info or "pair not found".

- [ ] **Step 5: Commit**

```bash
git add scripts/ave_data_rest.py
git commit -m "feat(data-rest): add pair command for trading pair detail"
```

---

### Task 13: Reorganize SKILL.md and data-api-doc.md by functional groups

**Files:**
- Modify: `skills/data-rest/SKILL.md`
- Modify: `references/data-api-doc.md`

The commands should be grouped as follows:

| Group | Commands |
|-------|----------|
| **Token Discovery** | `search`, `search-details`, `platform-tokens`, `trending`, `rank-topics`, `ranks` |
| **Token Detail** | `token`, `price`, `risk`, `holders`, `main-tokens`, `chains` |
| **Kline / Charts** | `kline-token`, `kline-pair`, `kline-ondo` |
| **Transactions** | `txs`, `liq-txs`, `tx-detail` |
| **Pair** | `pair` |
| **Wallet / Address** | `address-txs`, `address-pnl`, `wallet-tokens`, `wallet-info`, `smart-wallets` |
| **Signals** | `signals` |

- [ ] **Step 1: Rewrite the Operations section of SKILL.md**

Replace the flat `## Operations` section with grouped subsections. Keep the YAML frontmatter unchanged except update the `description` to mention new capabilities (wallet analysis, signals, liquidity, pair detail). The full replacement content:

```markdown
## Operations

### Token Discovery

#### Search tokens
Find tokens by keyword, symbol, or contract.
\`\`\`bash
python scripts/ave_data_rest.py search --keyword <keyword> [--chain <chain>] [--limit 20]
\`\`\`

#### Search token details (batch)
Look up full details for up to 50 tokens by address-chain.
\`\`\`bash
python scripts/ave_data_rest.py search-details --tokens <addr1>-<chain1> [<addr2>-<chain2> ...]
\`\`\`

#### Platform tokens
Browse launchpad or topic feeds by platform tag.
\`\`\`bash
python scripts/ave_data_rest.py platform-tokens --platform <platform>
\`\`\`

#### Trending
Get trending tokens for a chain.
\`\`\`bash
python scripts/ave_data_rest.py trending --chain <chain> [--page 0] [--page-size 20]
\`\`\`

#### Rank topics
List available ranking topics.
\`\`\`bash
python scripts/ave_data_rest.py rank-topics
\`\`\`

#### Ranks
Get ranked tokens for a topic.
\`\`\`bash
python scripts/ave_data_rest.py ranks --topic <topic>
\`\`\`

### Token Detail

#### Token detail
Get price, liquidity, volume, pairs, and token summary.
\`\`\`bash
python scripts/ave_data_rest.py token --address <contract_address> --chain <chain>
\`\`\`

#### Token prices (batch)
Batch price lookup for up to 200 tokens.
\`\`\`bash
python scripts/ave_data_rest.py price --tokens <addr1>-<chain1> <addr2>-<chain2> ...
\`\`\`

#### Risk report
Run the contract security and honeypot report.
\`\`\`bash
python scripts/ave_data_rest.py risk --address <token> --chain <chain>
\`\`\`

#### Holders
Get token holders with sorting.
\`\`\`bash
python scripts/ave_data_rest.py holders --address <token> --chain <chain> [--limit 100] [--sort-by balance] [--order desc]
\`\`\`

#### Main tokens
Get the main or native tokens for a chain.
\`\`\`bash
python scripts/ave_data_rest.py main-tokens --chain <chain>
\`\`\`

#### Chains
List supported chain identifiers.
\`\`\`bash
python scripts/ave_data_rest.py chains
\`\`\`

### Kline / Charts

#### Kline by token
Get OHLCV candles by token address.
\`\`\`bash
python scripts/ave_data_rest.py kline-token --address <token> --chain <chain> [--interval 60] [--size 24]
\`\`\`

#### Kline by pair
Get OHLCV candles by pair address.
\`\`\`bash
python scripts/ave_data_rest.py kline-pair --address <pair> --chain <chain> [--interval 60] [--size 24]
\`\`\`

#### Kline Ondo
Get Ondo-mapped kline data by pair address or ticker.
\`\`\`bash
python scripts/ave_data_rest.py kline-ondo --pair <pair_address-chain or ticker> [--interval 60] [--size 24]
\`\`\`

### Transactions

#### Swap transactions
Get recent swap transactions for a pair.
\`\`\`bash
python scripts/ave_data_rest.py txs --address <pair> --chain <chain>
\`\`\`

#### Liquidity transactions
Get liquidity add/remove/create events for a pair.
\`\`\`bash
python scripts/ave_data_rest.py liq-txs --address <pair> --chain <chain> [--type all] [--limit 100]
\`\`\`

#### Transaction detail
Look up a specific transaction by hash.
\`\`\`bash
python scripts/ave_data_rest.py tx-detail --chain <chain> --account <address> --tx-hash <hash>
\`\`\`

### Pair

#### Pair detail
Get trading pair information.
\`\`\`bash
python scripts/ave_data_rest.py pair --address <pair> --chain <chain>
\`\`\`

### Wallet / Address

#### Wallet swap history
Get swap transactions for a wallet address.
\`\`\`bash
python scripts/ave_data_rest.py address-txs --wallet <address> --chain <chain> [--token <token>]
\`\`\`

#### Wallet token PnL
Get profit/loss for a wallet on a specific token.
\`\`\`bash
python scripts/ave_data_rest.py address-pnl --wallet <address> --chain <chain> --token <token>
\`\`\`

#### Wallet token holdings
Get paginated token holdings for a wallet.
\`\`\`bash
python scripts/ave_data_rest.py wallet-tokens --wallet <address> --chain <chain> [--sort last_txn_time] [--hide-sold] [--blue-chips]
\`\`\`

#### Wallet overview
Get wallet summary and stats.
\`\`\`bash
python scripts/ave_data_rest.py wallet-info --wallet <address> --chain <chain>
\`\`\`

#### Smart wallet discovery
List smart wallets with profit-tier filters.
\`\`\`bash
python scripts/ave_data_rest.py smart-wallets --chain <chain> [--keyword <keyword>]
\`\`\`

### Signals

#### Public trading signals
Get public trading signal feed.
\`\`\`bash
python scripts/ave_data_rest.py signals [--chain solana] [--page-size 10] [--page-no 1]
\`\`\`
```

- [ ] **Step 2: Update the SKILL.md description field in frontmatter**

Add to the `description` field after "Run a contract security/risk detection report":

```yaml
  - Get wallet swap history, token PnL, and holdings
  - Get wallet overview and smart wallet discovery
  - Get public trading signals
  - Get liquidity transactions and transaction details for a pair
  - Get trading pair detail
  - Get Ondo-mapped kline data
  - Batch search token details by address-chain list
```

- [ ] **Step 3: Update `references/data-api-doc.md` with new endpoint entries**

Add these sections after the existing "Contract Risk Detection" section, grouped under a `## Wallet / Address Endpoints` heading:

```markdown
## Wallet / Address Endpoints

### Address Swap History
\`\`\`
GET /v2/address/tx?wallet_address={addr}&chain={chain}
\`\`\`
Params: `wallet_address` (required), `chain` (required), `token_address`, `from_time` (unix), `last_time` (RFC3339 cursor), `last_id`, `page_size` (max 100)

### Address Token PnL
\`\`\`
GET /v2/address/pnl?wallet_address={addr}&chain={chain}&token_address={token}
\`\`\`
All three params required.

### Wallet Token Holdings
\`\`\`
GET /v2/address/walletinfo/tokens?wallet_address={addr}&chain={chain}
\`\`\`
Params: `wallet_address` (required), `chain` (required), `sort` (default: last_txn_time), `sort_dir`, `pageSize`, `pageNO`, `hide_sold` (0/1), `hide_small` (USD threshold), `blue_chips` (0/1)

### Wallet Overview
\`\`\`
GET /v2/address/walletinfo?wallet_address={addr}&chain={chain}
\`\`\`
Params: `wallet_address` (required), `chain` (required), `self_address` (optional, for relative stats)

### Smart Wallet List
\`\`\`
GET /v2/address/smart_wallet/list?chain={chain}
\`\`\`
Params: `chain` (required), `keyword`, `sort`, `sort_dir`, plus profit-tier range filters (profit_above_900_percent_num_min/max, profit_300_900_percent_num_min/max, etc.)

## Additional Endpoints

### Token Search Details (Batch)
\`\`\`
POST /v2/tokens/search
Body: { "token_ids": ["address-chain", ...] }
\`\`\`
Max 50 tokens per request. Returns full token detail for each.

### Token Holders (Full)
\`\`\`
GET /v2/tokens/holders/{token_address}-{chain}?limit={n}&sort_by={field}&order={dir}
\`\`\`
Params: `limit` (1-100, default 100), `sort_by` (balance|percentage, default balance), `order` (asc|desc, default desc)

### Ondo Kline
\`\`\`
GET /v2/klines/pair/ondo/{pair_address-chain or ticker}?interval={min}&limit={n}
\`\`\`
Valid intervals: 1, 5, 15, 60, 240, 720, 1440

### Liquidity Transactions
\`\`\`
GET /v2/txs/liq/{pair_address}-{chain}?type={type}&limit={n}&sort={dir}
\`\`\`
Params: `type` (addLiquidity|removeLiquidity|createPair|all), `limit` (max 300), `from_time`, `to_time`, `sort` (asc|desc)

### Transaction Detail
\`\`\`
GET /v2/txs/detail?chain={chain}&account_address={addr}&tx_hash={hash}
\`\`\`
Params: all three required. Optional: `start_from`, `end_at` (unix), `limit`

### Pair Detail
\`\`\`
GET /v2/pairs/{pair_address}-{chain}
\`\`\`

### Public Trading Signals
\`\`\`
GET /v2/signals/public/list?chain={chain}&pageSize={n}&pageNO={n}
\`\`\`
Params: `chain` (default: solana), `pageSize` (max 50), `pageNO` (default: 1)
```

- [ ] **Step 4: Commit**

```bash
git add skills/data-rest/SKILL.md references/data-api-doc.md
git commit -m "docs: reorganize data-rest commands by function and document new endpoints"
```

---

### Task 14: Final verification

- [ ] **Step 1: Run `python scripts/ave_data_rest.py --help` and verify all 25 commands appear**

Expected commands: `search`, `search-details`, `platform-tokens`, `token`, `price`, `kline-token`, `kline-pair`, `kline-ondo`, `holders`, `txs`, `liq-txs`, `tx-detail`, `trending`, `rank-topics`, `ranks`, `risk`, `chains`, `main-tokens`, `pair`, `address-txs`, `address-pnl`, `wallet-tokens`, `wallet-info`, `smart-wallets`, `signals`

- [ ] **Step 2: Run CI checks**

```bash
bash scripts/ci/check-metadata.sh
bash scripts/ci/check-install-surfaces.sh
```

Expected: both pass.

- [ ] **Step 3: Commit any fixes if CI checks surface issues**

```bash
git add -A && git commit -m "fix: address CI check findings"
```

---

### Task 15: Live API verification with Docker and trade.env credentials

**Files:**
- Read only: `/Users/wgx731/Code/secrets/ai/trade.env` (source credentials, never commit)

Load credentials from the env file and run one representative command per functional group via Docker against the live API. This confirms the endpoints work end-to-end.

- [ ] **Step 1: Source credentials and build Docker image**

```bash
set -a && source /Users/wgx731/Code/secrets/ai/trade.env && set +a
docker build -f scripts/Dockerfile.txt -t ave-cloud .
```

Verify: `echo $AVE_API_KEY` should print a non-empty key.

- [ ] **Step 2: Token Discovery - test `search`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py search --keyword PEPE --chain bsc --limit 3
```

Expected: JSON with `"status": 1` and token list.

- [ ] **Step 3: Token Discovery - test `search-details`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py search-details --tokens 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c-bsc
```

Expected: JSON with `"status": 1` and token detail array.

- [ ] **Step 4: Token Detail - test `holders` (replaced endpoint)**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py holders --address 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c --chain bsc --limit 5 --sort-by balance --order desc
```

Expected: JSON with `"status": 1` and holder data with sort applied.

- [ ] **Step 5: Kline - test `kline-ondo`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py kline-ondo --pair BTC-USD --interval 60 --size 5
```

Expected: JSON response (either kline data or "pair not found" success).

- [ ] **Step 6: Transactions - test `liq-txs`**

First find a known BSC pair address from a token detail call, then:

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py liq-txs --address <pair_from_step_above> --chain bsc --limit 3 --type all
```

Expected: JSON with `"status": 1`.

- [ ] **Step 7: Transactions - test `tx-detail`**

Use a tx_hash and account_address from the `txs` or `address-txs` output:

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py tx-detail --chain bsc --account <account> --tx-hash <hash>
```

Expected: JSON with `"status": 1`.

- [ ] **Step 8: Pair - test `pair`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py pair --address <pair_address> --chain bsc
```

Expected: JSON with pair info.

- [ ] **Step 9: Wallet - test `address-txs`**

Use a known active BSC wallet:

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py address-txs --wallet <wallet_address> --chain bsc
```

Expected: JSON with `"status": 1` and swap tx list.

- [ ] **Step 10: Wallet - test `address-pnl`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py address-pnl --wallet <wallet_address> --chain bsc --token 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c
```

Expected: JSON with PnL data.

- [ ] **Step 11: Wallet - test `wallet-tokens`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py wallet-tokens --wallet <wallet_address> --chain bsc
```

Expected: JSON with token holdings.

- [ ] **Step 12: Wallet - test `wallet-info`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py wallet-info --wallet <wallet_address> --chain bsc
```

Expected: JSON with wallet overview.

- [ ] **Step 13: Wallet - test `smart-wallets`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py smart-wallets --chain solana
```

Expected: JSON with smart wallet list.

- [ ] **Step 14: Signals - test `signals`**

```bash
docker run --rm -e AVE_API_KEY=$AVE_API_KEY -e API_PLAN=$API_PLAN -e AVE_USE_DOCKER=true --entrypoint python ave-cloud scripts/ave_data_rest.py signals --chain solana --page-size 3
```

Expected: JSON with `"status": 1` and signal list.

- [ ] **Step 15: Record results**

For each command, note pass/fail. If any command returns an unexpected error (not "not found" type responses, which are valid), investigate and fix the command function before proceeding.

**Important:** Do not commit the env file or echo credentials. All test commands use Docker with `-e` flags to pass credentials securely.
