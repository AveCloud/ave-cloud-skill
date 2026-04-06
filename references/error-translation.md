# Error Translation

Translate low-level API failures into direct operator guidance. Prefer the translated explanation in responses, with the raw error as supporting detail only when useful.

## Auth

| Raw issue | Explanation | Applies to |
|---|---|---|
| missing API key / auth failed | Credentials missing or invalid; check `AVE_API_KEY` | all |
| HMAC signature mismatch | Secret key wrong; regenerate `AVE_SECRET_KEY` at cloud.ave.ai | proxy-wallet |
| user account not exist or deactivated | Proxy wallet account missing or inactive | proxy-wallet |

## Network & Rate Limits

| Raw issue | Explanation | Applies to |
|---|---|---|
| HTTP 429 / rate limit exceeded | Too many requests; wait and retry after the rate limit window resets | all |
| RPC connection refused / timeout | RPC endpoint unreachable; try a different RPC URL | chain-wallet |
| connection closed / EOF | WebSocket disconnected; reconnect or restart the REPL | data-wss |
| pipe not found / FIFO error | Named pipe `/tmp/ave_pipe` missing; restart the server container | data-wss |

## Data Queries

| Raw issue | Explanation | Applies to |
|---|---|---|
| invalid token_ids | Token identifier format or filter combination not accepted | data-rest |
| token not found | AVE has no matching token record for that chain/address | data-rest |
| empty holder list on a known token | Endpoint returned no holder data; treat as data unavailability, not proof of zero holders | data-rest |
| unsupported chain | Chain ID not supported by this endpoint | data-rest |
| kline returns more points than requested | API ignored `limit`; client-side trimming applied automatically | data-rest |
| empty risk report on a valid token | Risk endpoint has no data for this token; do not treat as "safe" | data-rest |

## Trade Execution

| Raw issue | Explanation | Applies to |
|---|---|---|
| unsupported parameter / invalid parameter | Parameter combination not accepted by PROD | chain-wallet, proxy-wallet |
| `Invalid parameter: feeRecipientRate` with only `feeRecipient` set | Pair `feeRecipient` with `feeRecipientRate`, or remove both | chain-wallet |
| insufficient balance / insufficient gas | Wallet needs more spend token or native gas token | chain-wallet, proxy-wallet |
| approval required / allowance too low | Approve the ERC-20 token first, then retry the sell or spend | chain-wallet, proxy-wallet |
| route too small / min notional failure | Trade size below route minimum; increase size slightly | chain-wallet, proxy-wallet |
| RPC required for `swap-evm` | Provide `--rpc-url` or set the chain-specific RPC env | chain-wallet |
| missing signing envs | Set `AVE_MNEMONIC` or the per-chain private key env | chain-wallet |
| transaction reverted / execution failed | On-chain tx failed; check slippage, gas, or token tax | chain-wallet |
| HTTP 200 with JSON error status | Treat as failed API call, not success | chain-wallet |
| `gasLimit` returned as 0 | CLI auto-estimates gas with 1.3x buffer; if still fails, increase manually | chain-wallet |
| transaction not found / approve not found | Requested order or approval ID does not exist | proxy-wallet |
| success with empty cancel response | Cancel accepted, but no active order data to return | proxy-wallet |
| order status `error` in WebSocket push | Check `errorMessage` in push event for root cause | proxy-wallet |

## WebSocket

| Raw issue | Explanation | Applies to |
|---|---|---|
| plan not supported | Feature requires a higher API plan tier (pro for WSS) | data-wss, proxy-wallet |
| subscribe failed / unknown topic | Subscription topic or address format not accepted | data-wss |
| server not running | Docker WSS daemon must be started with `start-server` first | data-wss |
