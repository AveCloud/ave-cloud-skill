# Ave Cloud Bot Trade API Documentation

**Source:** https://docs-bot-api.ave.ai/
**Base URL:** `https://bot-api.ave.ai`
**Last Updated:** 2026-02-28

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Chain Wallet Trading REST API](#chain-wallet-trading-rest-api)
   - [Authentication](#chain-wallet-authentication)
   - [Quote API](#quote-api)
   - [EVM (BSC/ETH/Base) Trading](#evm-trading)
   - [Solana Trading](#solana-trading)
3. [Proxy Wallet (Bot Wallet) Trading REST API](#proxy-wallet-trading-rest-api)
   - [Authentication & Signature](#proxy-wallet-authentication)
   - [Wallet Management](#wallet-management)
   - [Market Trading](#market-trading)
   - [Limit Trading](#limit-trading)
   - [Query Market Orders](#query-market-orders)
   - [Query Limit Orders](#query-limit-orders)
   - [Cancel Limit Order](#cancel-limit-order)
   - [Token Approval (EVM)](#token-approval-evm)
   - [Transfer](#transfer)
4. [WebSocket Push Notifications](#websocket-push)
5. [Error Codes](#error-codes)
6. [Change Log](#change-log)

---

## Getting Started

Register an account at **https://cloud.ave.ai/** to activate API access.

### Pricing Tiers

| Feature | Free | Level 1 | Level 2 | Enterprise |
|---------|------|---------|---------|------------|
| Chain Wallet API | ✓ | ✓ | ✓ | ✓ |
| Proxy Wallet API | ✗ | ✓ | ✓ | ✓ |
| Write Request Rate Limit | 1 TPS | 5 TPS | 20 TPS | Custom |
| Max Proxy Wallets | — | 500 | 5,000 | Custom |

### Fees & Rebates

| | Proxy Wallet API | Chain Wallet API |
|--|-----------------|-----------------|
| Trading Fee | 0.8% | 0.6% |
| Rebate (to `feeRecipient`) | 25% | 20% |

**Proxy Wallet API** requires Level 1 or above, plus an Ave Bot wallet account for receiving rebates.
**Chain Wallet API** is available on all tiers including free.

---

## Chain Wallet Trading REST API

Chain wallets are user-controlled (self-custody) wallets. Ave does not hold private keys. You must sign transactions client-side before sending.

### Chain Wallet Authentication

All chain wallet requests require the following header:

| Header | Required | Description |
|--------|----------|-------------|
| `AVE-ACCESS-KEY` | Yes | Your API access key |

---

### Quote API

Get an estimated output amount for a given input.

**`POST /v1/thirdParty/chainWallet/getAmountOut`**

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | Chain name: `bsc` / `eth` / `base` / `solana` |
| `inAmount` | string | Yes | Input amount in smallest unit (e.g., wei or lamports) |
| `inTokenAddress` | string | Yes | Input token address (must be native coin or USDT) |
| `outTokenAddress` | string | Yes | Output token address (must be native coin or USDT) |
| `swapType` | string | Yes | Trade direction: `buy` / `sell` |

#### Request Example

```json
{
  "chain": "bsc",
  "inAmount": "10000000",
  "inTokenAddress": "0x55d398326f99059ff775485246999027b3197955",
  "outTokenAddress": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
  "swapType": "buy"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | int | Status code |
| `msg` | string | Response message |
| `data.estimateOut` | string | Estimated output amount |
| `data.decimals` | int | Output token decimals |
| `data.spender` | string | Spender contract address requiring approval |

#### Response Example

```json
{
  "status": 200,
  "msg": "Success",
  "data": {
    "estimateOut": "3285",
    "decimals": 18,
    "spender": "0x0fe1face5ec9e4c34c701dff0ba3a1c22e2cc583"
  }
}
```

---

### EVM Trading

Supports BSC, Ethereum, and Base chains.

**Trading flow:**
1. Approve the input token to the Router contract (skip for native coins)
2. Call **Create EVM Transaction** to get transaction parameters
3. Sign the transaction client-side
4. Call **Send Signed EVM Transaction** (or broadcast yourself)

**Router Contract Addresses:**

| Chain | Address |
|-------|---------|
| BSC | `0x4eadd85e7a6bb368eb1e3fb22b56ecac79e9058f` |
| ETH | `0x77acf9c55106e20fa41f418e2453cdae7ba62f2f` |
| Base | `0x574bb43779bfa604f3c5a7d35f82b0dcd9bcf0f9` |

For transaction signing, see [ethers.js docs](https://docs.ethers.org/v6/api/providers/#Signer-signTransaction).

---

#### Create EVM Transaction

Constructs a transaction ready to be signed.

**`POST /v1/thirdParty/chainWallet/createEvmTx`**

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `bsc` / `eth` / `base` |
| `creatorAddress` | string | Yes | Wallet address initiating the transaction |
| `inAmount` | string | Yes | Input amount in smallest unit |
| `inTokenAddress` | string | Yes | Input token address (native coin or USDT) |
| `outTokenAddress` | string | Yes | Output token address (native coin or USDT) |
| `swapType` | string | Yes | `buy` / `sell` |
| `slippage` | string | Yes | Slippage in bps (10000 = 100%) |
| `feeRecipient` | string | No | Address to receive trading rebate |
| `autoSlippage` | boolean | No | Enable auto slippage (default: `false`). Overrides `slippage` when enabled |

##### Request Example

```json
{
  "chain": "bsc",
  "creatorAddress": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1",
  "inAmount": "1000000",
  "inTokenAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "outTokenAddress": "0xb4357054c3da8d46ed642383f03139ac7f090343",
  "swapType": "buy",
  "slippage": "500",
  "feeRecipient": "0x15a3d97326265d870FA789Cc66052E753f1003d5",
  "autoSlippage": true
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | int | Status code |
| `msg` | string | Response message |
| `data.chain` | string | Chain name |
| `data.creatorAddress` | string | Sender address |
| `data.swapType` | string | Trade direction |
| `data.inTokenAddress` | string | Input token address |
| `data.outTokenAddress` | string | Output token address |
| `data.toAddress` | string | Transaction `to` address |
| `data.txContent` | string | Transaction input data (hex) |
| `data.slippage` | string | Applied slippage in bps |
| `data.minReturn` | string | Minimum acceptable output amount |
| `data.inAmount` | string | Input amount |
| `data.estimateOut` | string | Estimated output amount |
| `data.gasLimit` | string | Gas limit |
| `data.amms` | string[] | AMM route info |
| `data.createPrice` | string | Token price at time of creation (USD) |
| `data.requestTxId` | string | Transaction request ID (pass to send endpoint) |

##### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": {
    "chain": "bsc",
    "creatorAddress": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1",
    "swapType": "buy",
    "inTokenAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "outTokenAddress": "0xa5e4ccf218cef628c85364253e5432d2cf18c87e",
    "toAddress": "0xa5e4ccf218cef628c85364253e5432d2cf18c87e",
    "txContent": "0x7ff36ab5...",
    "slippage": "500",
    "minReturn": "1000000",
    "inAmount": "1000000000000000000",
    "estimateOut": "1050000",
    "gasLimit": "100000",
    "amms": ["cakev2", "cakev3"],
    "createPrice": "15.5",
    "requestTxId": "123456789"
  }
}
```

---

#### Send Signed EVM Transaction

**`POST /v1/thirdParty/chainWallet/sendSignedEvmTx`**

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `bsc` / `eth` / `base` |
| `requestTxId` | string | Yes | `requestTxId` returned from `createEvmTx` |
| `signedTx` | string | Yes | Signed transaction (hex-encoded) |
| `useMev` | boolean | No | Enable MEV protection |

##### Request Example

```json
{
  "chain": "bsc",
  "requestTxId": "123456789",
  "signedTx": "0xd6afd6bf...",
  "useMev": false
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | int | Status code |
| `msg` | string | Response message |
| `data.hash` | string | Transaction hash |
| `data.err` | string | Error message from chain (if any) |

##### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": {
    "hash": "0xc2b152898e375e003bded19871dd13bee8991183de9e83dca159fcb8f5334aab",
    "err": ""
  }
}
```

---

### Solana Trading

**Trading flow:**
1. Call **Create Solana Transaction** to get transaction parameters
2. Sign the transaction client-side
3. Call **Send Signed Solana Transaction** (or broadcast yourself)

#### Golang Transaction Signing Example

```go
func signSolTx(privateKey solana.PrivateKey, txContent string) (string, error) {
    var tx = new(solana.Transaction)
    err := tx.Message.UnmarshalBase64(txContent)
    if err != nil {
        return "", err
    }
    _, err = tx.Sign(func(key solana.PublicKey) *solana.PrivateKey {
        if privateKey.PublicKey().Equals(key) {
            return &privateKey
        }
        return nil
    })
    if err != nil {
        return "", err
    }
    return tx.MustToBase64(), nil
}
```

---

#### Create Solana Transaction

**`POST /v1/thirdParty/chainWallet/createSolanaTx`**

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `creatorAddress` | string | Yes | Wallet address initiating the transaction |
| `inAmount` | string | Yes | Input amount in lamports (1 SOL = `"1000000000"`) |
| `inTokenAddress` | string | Yes | Input token address. For buy: must be SOL/USDT/USDC (use `"sol"` for SOL) |
| `outTokenAddress` | string | Yes | Output token address. For sell: must be SOL/USDT/USDC (use `"sol"` for SOL) |
| `swapType` | string | Yes | `buy` / `sell` |
| `slippage` | string | Yes | Slippage in bps (10000 = 100%) |
| `fee` | string | Yes | Network + node priority fee in lamports. Ave auto-allocates bundle tip and priority fee |
| `useMev` | boolean | No | Enable MEV protection (default: `false`) |
| `feeRecipient` | string | No | Address to receive trading rebate |
| `autoSlippage` | boolean | No | Enable auto slippage (default: `false`). Overrides `slippage` when enabled |

##### Request Example

```json
{
  "creatorAddress": "EgsEi74MPVo5zd3TaHrJuAmb5iRbNj2HyQEXVyp5HSJ8",
  "inAmount": "1000000",
  "inTokenAddress": "sol",
  "outTokenAddress": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
  "swapType": "buy",
  "slippage": "500",
  "fee": "50000000",
  "useMev": true,
  "feeRecipient": "wfvDFTYEqsJQoaVGx7UUWcUU5r7SGNCcZcH24z8Jyc5",
  "autoSlippage": false
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | int | Status code |
| `msg` | string | Response message |
| `data.creatorAddress` | string | Sender address |
| `data.swapType` | string | Trade direction |
| `data.inTokenAddress` | string | Input token address |
| `data.outTokenAddress` | string | Output token address |
| `data.txContent` | string | Base64-encoded transaction message to sign |
| `data.slippage` | string | Applied slippage in bps |
| `data.minReturn` | string | Minimum acceptable output amount |
| `data.inAmount` | string | Input amount |
| `data.estimateOut` | string | Estimated output amount |
| `data.priorityFee` | string | Priority fee in lamports |
| `data.bundleTip` | string | Bundle tip in lamports |
| `data.amms` | string[] | AMM route info |
| `data.createPrice` | string | Token price at creation time (USD) |
| `data.requestTxId` | string | Transaction request ID (pass to send endpoint) |

---

#### Send Signed Solana Transaction

**`POST /v1/thirdParty/chainWallet/sendSignedSolanaTx`**

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `requestTxId` | string | Yes | `requestTxId` returned from `createSolanaTx` |
| `signedTx` | string | Yes | Signed transaction (base64-encoded) |
| `useMev` | boolean | No | Enable MEV protection (default: `false`) |

##### Request Example

```json
{
  "requestTxId": "ddee4ce002944fc79177e7d86df93daa",
  "signedTx": "ATINUBypvT3cGpXqPcMiayNuv3l8Vk2...",
  "useMev": false
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | int | Status code |
| `msg` | string | Response message |
| `data.hash` | string | Transaction hash |
| `data.bundleId` | string | Jito bundle ID (only when MEV is enabled) |
| `data.err` | string | Error message from chain (if any) |

##### Response Example

```json
{
  "status": 200,
  "msg": "Success",
  "data": {
    "hash": "2MJFSf5LAqv11DV1JhkaaXy86qarqd7SsDo9wGPZ7ZXUf4uunGM9LNYLa6kXqQYqKSUXtj72Hs5E9kfeP6eBcAdW",
    "bundleId": "ea8d542b9a5aeaa9b385a2aae9c02460377e6d95adc0a338c4a250658efbd172",
    "err": ""
  }
}
```

---

## Proxy Wallet Trading REST API

Proxy wallets (Bot wallets) are server-side wallets fully managed by Ave. Users do not need to sign transactions — all operations are executed server-side.

> **Requires Level 1 or above.** See [Getting Started](#getting-started).

### Proxy Wallet Authentication

All proxy wallet API requests require **HMAC-SHA256 signature authentication**.

#### Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `AVE-ACCESS-KEY` | Yes | Your API access key |
| `AVE-ACCESS-TIMESTAMP` | Yes | Request timestamp (UTC, RFC3339Nano format) |
| `AVE-ACCESS-SIGN` | Yes | Request signature (see below) |

#### Signature Generation

**Formula:**
```
SignatureString = Timestamp + HTTP_METHOD + RequestPath + RequestBody
Signature = Base64(HMAC-SHA256(ApiSecret, SignatureString))
```

**Rules:**
- `HTTP_METHOD` must be uppercase (e.g., `GET`, `POST`)
- If request body is JSON, sort object keys alphabetically before signing
- Request body must not contain spaces or newlines
- GET query parameters are **not** included in the signature

#### Code Examples

<details>
<summary><strong>Go</strong></summary>

```go
func GenerateSignature(apiSecret, method, requestPath string, body interface{}) (string, string, error) {
    timestamp := time.Now().UTC().Format(time.RFC3339Nano)
    method = strings.ToUpper(strings.TrimSpace(method))
    requestPath = strings.TrimSpace(requestPath)
    message := timestamp + method + requestPath

    if body != nil {
        switch v := body.(type) {
        case string:
            message += strings.TrimSpace(v)
        case []byte:
            message += strings.TrimSpace(string(v))
        default:
            jsonBytes, err := json.Marshal(body)
            if err != nil {
                return "", "", fmt.Errorf("failed to marshal body: %v", err)
            }
            var jsonMap map[string]interface{}
            if err := json.Unmarshal(jsonBytes, &jsonMap); err != nil {
                return "", "", fmt.Errorf("failed to unmarshal body: %v", err)
            }
            sortedBytes, err := json.Marshal(jsonMap)
            if err != nil {
                return "", "", fmt.Errorf("failed to marshal sorted body: %v", err)
            }
            message += string(sortedBytes)
        }
    }

    h := hmac.New(sha256.New, []byte(apiSecret))
    h.Write([]byte(message))
    signature := base64.StdEncoding.EncodeToString(h.Sum(nil))
    return signature, timestamp, nil
}
```

</details>

<details>
<summary><strong>Python</strong></summary>

```python
import hmac
import hashlib
import json
import base64
from datetime import datetime
from typing import Union, Dict, Any

def generate_signature(api_secret: str, method: str, request_path: str,
                       body: Union[str, dict, None] = None) -> Dict[str, Any]:
    timestamp = datetime.utcnow().isoformat() + 'Z'
    method = method.upper().strip()
    request_path = request_path.strip()
    message = timestamp + method + request_path

    if body:
        if isinstance(body, dict):
            message += json.dumps(body, sort_keys=True, separators=(',', ':'))
        else:
            message += str(body).strip()

    hmac_obj = hmac.new(
        key=api_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    signature_b64 = base64.b64encode(hmac_obj.digest()).decode('utf-8')

    return {
        'signature': signature_b64,
        'timestamp': timestamp,
        'headers': {
            'AVE-ACCESS-SIGN': signature_b64,
            'AVE-ACCESS-TIMESTAMP': timestamp,
        }
    }
```

</details>

<details>
<summary><strong>Java</strong></summary>

```java
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;

public class AveSignature {
    public static Map<String, String> generateHeaders(String apiSecret, String apiKey,
            String method, String requestPath, Object body) throws Exception {
        String timestamp = Instant.now().toString();
        method = method.toUpperCase().trim();
        requestPath = requestPath.trim();
        StringBuilder message = new StringBuilder()
                .append(timestamp).append(method).append(requestPath);

        if (body != null) {
            ObjectMapper mapper = new ObjectMapper();
            String jsonStr = mapper.writeValueAsString(body);
            Map<String, Object> jsonMap = mapper.readValue(jsonStr,
                    new TypeReference<Map<String, Object>>() {});
            Map<String, Object> sortedMap = sortMapRecursive(jsonMap);
            message.append(mapper.writeValueAsString(sortedMap));
        }

        Mac hmac = Mac.getInstance("HmacSHA256");
        hmac.init(new SecretKeySpec(apiSecret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        String signature = Base64.getEncoder().encodeToString(
                hmac.doFinal(message.toString().getBytes(StandardCharsets.UTF_8)));

        Map<String, String> headers = new HashMap<>();
        headers.put("AVE-ACCESS-KEY", apiKey);
        headers.put("AVE-ACCESS-TIMESTAMP", timestamp);
        headers.put("AVE-ACCESS-SIGN", signature);
        return headers;
    }

    private static Map<String, Object> sortMapRecursive(Map<String, Object> map) {
        Map<String, Object> sorted = new TreeMap<>(map);
        for (Map.Entry<String, Object> entry : sorted.entrySet()) {
            if (entry.getValue() instanceof Map) {
                entry.setValue(sortMapRecursive((Map<String, Object>) entry.getValue()));
            }
        }
        return sorted;
    }
}
```

</details>

---

### Wallet Management

#### Get Users by Assets ID

**`GET /v1/thirdParty/user/getUserByAssetsId`**

| Query Parameter | Type | Required | Description |
|----------------|------|----------|-------------|
| `assetsIds` | string | No | Comma-separated asset IDs. Returns all users in the organization if omitted |

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | int | Status code |
| `msg` | string | Response message |
| `data` | array | List of user objects |
| `data[].assetsId` | string | User asset ID |
| `data[].status` | string | Account status (`enabled` / `disabled`). Applies to `self` type only |
| `data[].type` | string | `self`: user-created via Ave app; `delegate`: created via API |
| `data[].assetsName` | string | Sub-wallet name |
| `data[].addressList` | array | Wallet addresses per chain |

##### Response Example

```json
{
  "status": 200,
  "msg": "Success",
  "data": [
    {
      "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
      "status": "enabled",
      "type": "self",
      "assetsName": "abc",
      "addressList": [
        { "chain": "bsc",    "address": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1" },
        { "chain": "eth",    "address": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1" },
        { "chain": "base",   "address": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1" },
        { "chain": "solana", "address": "8a5wPUzsUxkjxTew9cVTynKsVa1ZDFK4Ex5bQo5NsrN8" }
      ]
    }
  ]
}
```

---

#### Generate Wallet

Creates a new delegate-type proxy wallet.

**`POST /v1/thirdParty/user/generateWallet`**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assetsName` | string | Yes | Name for the sub-wallet |
| `returnMnemonic` | boolean | No | Return mnemonic phrase (default: `false`) |

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data[].assetsId` | string | New user asset ID |
| `data[].mnemonic` | string | Mnemonic phrase (Base64-encoded). Only included when `returnMnemonic: true` |
| `data[].addressList` | array | Wallet addresses per chain |

##### Response Example

```json
{
  "status": 200,
  "msg": "Success",
  "data": [
    {
      "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
      "mnemonic": "aBcdeface...",
      "addressList": [
        { "chain": "bsc",    "address": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1" },
        { "chain": "eth",    "address": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1" },
        { "chain": "base",   "address": "0xd6afd6bfade550ad3959460212e2fd1624b8cac1" },
        { "chain": "solana", "address": "8a5wPUzsUxkjxTew9cVTynKsVa1ZDFK4Ex5bQo5NsrN8" }
      ]
    }
  ]
}
```

---

#### Delete Wallet

Deletes one or more delegate-type proxy wallets. Cannot delete `self`-type wallets.

**`POST /v1/thirdParty/user/deleteWallet`**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assetsIds` | string[] | Yes | Array of asset IDs to delete |

##### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": {
    "assetsIds": ["0e7ad94f7c554f3ca46d281a8695b637"]
  }
}
```

---

### Market Trading

Executes an immediate (market) swap.

**`POST /v1/thirdParty/tx/sendSwapOrder`**

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `solana` / `bsc` / `base` / `eth` |
| `assetsId` | string | Yes | User asset ID |
| `inTokenAddress` | string | Yes | Input token address |
| `outTokenAddress` | string | Yes | Output token address |
| `inAmount` | string | Yes | Input amount in token's smallest unit (e.g., `"1000000"` for 1 USDT with 6 decimals) |
| `swapType` | string | Yes | `buy` / `sell` |
| `slippage` | string | Yes | Slippage in bps (10000 = 100%) |
| `useMev` | boolean | Yes | Enable MEV protection |
| `gas` | string | No | Solana gas fee in lamports (required for Solana) |
| `extraGas` | string | No | EVM extra gas in wei added on top of base fee (required for EVM chains) |
| `autoSlippage` | boolean | No | Enable auto slippage (overrides `slippage`). Default: `false` |
| `autoGas` | string | No | Auto gas tier: `low` / `average` / `high`. Overrides `gas`/`extraGas` when set |
| `autoSellConfig` | AutoSellConfig[] | No | Auto-sell rules (take-profit / stop-loss / trailing) |

#### AutoSellConfig Fields

| Field | Type | Description |
|-------|------|-------------|
| `priceChange` | string | Price change threshold in bps. Positive = profit target (e.g., `"5000"` = +50%), negative = stop-loss (e.g., `"-9000"` = -90%). For trailing type, this is the drawdown ratio (e.g., `"1000"` = 10% drawdown) |
| `sellRatio` | string | Percentage of tokens to sell in bps (10000 = 100%, 5000 = 50%) |
| `type` | string | `default`: trigger when price hits target; `trailing`: trigger when price peaks then drops by `priceChange` |

**AutoSellConfig rules:**
- Maximum 10 `default` type rules per order
- Maximum 1 `trailing` type rule per order
- Sell ratios are based on tokens received from the associated buy
- If all tokens are sold (manually or via auto-sell), remaining auto-sell orders are cancelled
- If triggered when balance < order amount, all remaining tokens are sold

#### Request Example

```json
{
  "chain": "solana",
  "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
  "inTokenAddress": "sol",
  "outTokenAddress": "3gWxcrL1KiZp9P6zVgNsiNnF8N3zYw2Vic4usW4ipump",
  "inAmount": "1000000",
  "swapType": "buy",
  "slippage": "500",
  "useMev": true,
  "autoSlippage": true,
  "autoGas": "average",
  "autoSellConfig": [
    { "priceChange": "-5000", "sellRatio": "10000", "type": "default" },
    { "priceChange": "5000",  "sellRatio": "5000",  "type": "default" },
    { "priceChange": "10000", "sellRatio": "5000",  "type": "default" },
    { "priceChange": "1000",  "sellRatio": "10000", "type": "trailing" }
  ]
}
```

> **Notes:**
> - Minimum buy `inAmount` is equivalent to 0.1 USD
> - When `useMev: true` on Solana, minimum gas is 0.001 SOL

#### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": {
    "id": "f50ddc7b87f04b538505cd3e6df6e78f"
  }
}
```

---

### Limit Trading

Places a limit order that executes when the token reaches the specified price.

**`POST /v1/thirdParty/tx/sendLimitOrder`**

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `solana` / `bsc` / `base` / `eth` |
| `assetsId` | string | Yes | User asset ID |
| `inTokenAddress` | string | Yes | Input token address |
| `outTokenAddress` | string | Yes | Output token address |
| `inAmount` | string | Yes | Input amount in token's smallest unit |
| `swapType` | string | Yes | `buy` / `sell` |
| `slippage` | string | Yes | Slippage in bps (10000 = 100%) |
| `useMev` | boolean | Yes | Enable MEV protection |
| `limitPrice` | string | Yes | Target execution price in USD |
| `gas` | string | No | Solana gas fee in lamports (required for Solana) |
| `extraGas` | string | No | EVM extra gas in wei (required for EVM chains) |
| `expireTime` | string | No | Order lifetime in seconds (max 604800 = 7 days, default: 604800) |
| `autoSlippage` | boolean | No | Enable auto slippage (overrides `slippage`). Default: `false` |
| `autoGas` | string | No | Auto gas tier: `low` / `average` / `high` |

#### Request Example

```json
{
  "chain": "solana",
  "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
  "inTokenAddress": "sol",
  "outTokenAddress": "3gWxcrL1KiZp9P6zVgNsiNnF8N3zYw2Vic4usW4ipump",
  "inAmount": "1000000",
  "swapType": "buy",
  "slippage": "500",
  "useMev": true,
  "limitPrice": "15.5",
  "expireTime": "86400",
  "autoSlippage": true,
  "autoGas": "average"
}
```

#### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": {
    "id": "f50ddc7b87f04b538505cd3e6df6e78f"
  }
}
```

---

### Query Market Orders

**`GET /v1/thirdParty/tx/getSwapOrder?chain={chain}&ids={ids}`**

| Query Parameter | Type | Required | Description |
|----------------|------|----------|-------------|
| `chain` | string | Yes | `solana` / `bsc` / `base` / `eth` |
| `ids` | string | Yes | Comma-separated order IDs |

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data[].id` | string | Order ID |
| `data[].status` | string | `generated` / `sent` / `confirmed` / `error` |
| `data[].chain` | string | Chain name |
| `data[].swapType` | string | `buy` / `sell` |
| `data[].txPriceUsd` | string | Execution price in USD |
| `data[].txHash` | string | Transaction hash |
| `data[].inAmount` | string | Input token amount |
| `data[].outAmount` | string | Output token amount |
| `data[].errorMessage` | string | Error message (if any) |

#### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": [
    {
      "id": "f50ddc7b87f04b538505cd3e6df6e78f",
      "status": "confirmed",
      "chain": "solana",
      "swapType": "buy",
      "txPriceUsd": "3.33",
      "txHash": "3BP18cjNaU4xpFpTsbZ688...",
      "inAmount": "1000000",
      "outAmount": "52752",
      "errorMessage": ""
    }
  ]
}
```

---

### Query Limit Orders

**`GET /v1/thirdParty/tx/getLimitOrder`**

| Query Parameter | Type | Required | Description |
|----------------|------|----------|-------------|
| `chain` | string | Yes | `solana` / `bsc` / `base` / `eth` |
| `assetsId` | string | Yes | User asset ID |
| `pageSize` | string | Yes | Number of results per page |
| `pageNo` | string | Yes | Page number (0-indexed) |
| `status` | string | No | Filter by status: `waiting` / `confirmed` / `error` / `auto_cancelled` / `cancelled` |
| `token` | string | No | Filter by token address |

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data[].id` | string | Order ID |
| `data[].status` | string | `generated` / `waiting` / `sent` / `confirmed` / `error` / `auto_cancelled` / `cancelled` |
| `data[].chain` | string | Chain name |
| `data[].swapType` | string | `buy` / `sell` / `takeprofit` / `stoploss` / `trailing` |
| `data[].inTokenAddress` | string | Input token address |
| `data[].outTokenAddress` | string | Output token address |
| `data[].txPriceUsd` | string | Execution price in USD |
| `data[].txHash` | string | Transaction hash |
| `data[].errorMessage` | string | Error message (if any) |
| `data[].limitPrice` | string | Limit price in USD |
| `data[].createPrice` | string | Token price when order was created (USD) |
| `data[].expireAt` | string | Expiration timestamp (Unix seconds) |
| `data[].inAmount` | string | Input token amount |
| `data[].outAmount` | string | Output token amount |
| `data[].trailingPriceChange` | string | Drawdown ratio for trailing orders (in bps) |
| `data[].autoSellTriggerHash` | string | Original tx hash that triggered auto-sell (for TP/SL/trailing orders) |

Results are sorted by order creation time (descending).

---

### Cancel Limit Order

Cancels one or more pending limit orders.

**`POST /v1/thirdParty/tx/cancelLimitOrder`**

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `solana` / `bsc` / `base` / `eth` |
| `ids` | string[] | Yes | Array of order IDs to cancel |

#### Request Example

```json
{
  "chain": "solana",
  "ids": [
    "f50ddc7b87f04b538505cd3e6df6e78f",
    "3155b751e0ff49c7955aef3018840777"
  ]
}
```

#### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": [
    "f50ddc7b87f04b538505cd3e6df6e78f",
    "3155b751e0ff49c7955aef3018840777"
  ]
}
```

`data` contains the list of successfully cancelled order IDs.

---

### Token Approval (EVM)

Before trading EVM tokens with a proxy wallet, the token must be approved for the router contract. Native coins do not require approval.

#### Approve Token

**`POST /v1/thirdParty/tx/approve`**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `bsc` / `eth` / `base` |
| `assetsId` | string | Yes | User asset ID |
| `tokenAddress` | string | Yes | Token address to approve |

The backend automatically selects the appropriate spender contract and approves the maximum amount (`uint256(-1)`).

##### Request Example

```json
{
  "chain": "bsc",
  "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
  "tokenAddress": "0xa5e4ccf218cef628c85364253e5432d2cf18c87e"
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data[].id` | string | Approval order ID |
| `data[].spender` | string | Spender contract address |
| `data[].amm` | string | AMM associated with the spender |

##### Response Example

```json
{
  "status": 0,
  "msg": "Success",
  "data": [
    {
      "id": "f50ddc7b87f04b538505cd3e6df6e78f",
      "spender": "0x296b00198dc7ec3410e12da814d9267bb8df506a",
      "amm": "cakev2"
    }
  ]
}
```

---

#### Get Approval Status

**`GET /v1/thirdParty/tx/getApprove?chain={chain}&ids={ids}`**

| Query Parameter | Type | Required | Description |
|----------------|------|----------|-------------|
| `chain` | string | Yes | `bsc` / `eth` / `base` |
| `ids` | string | Yes | Comma-separated approval order IDs |

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data[].id` | string | Approval order ID |
| `data[].status` | string | `generated` / `sent` / `confirmed` / `error` |
| `data[].chain` | string | Chain name |
| `data[].spender` | string | Spender contract address |
| `data[].token` | string | Token address |
| `data[].txHash` | string | Transaction hash |
| `data[].errorMessage` | string | Error message (if any) |

---

### Transfer

Transfers tokens from a delegate-type proxy wallet. Cannot be used with `self`-type wallets.

#### Send Transfer

**`POST /v1/thirdParty/tx/transfer`**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | string | Yes | `bsc` / `solana` / `base` / `eth` |
| `assetsId` | string | Yes | User asset ID |
| `fromAddress` | string | Yes | Source wallet address |
| `toAddress` | string | Yes | Destination wallet address |
| `tokenAddress` | string | Yes | Token address to transfer |
| `amount` | string | Yes | Amount in smallest unit (e.g., `"1000000000000000000"` for 1 USDT with 18 decimals) |
| `gas` | string | No | Gas fee in lamports (required for Solana) |
| `extraGas` | string | No | Extra gas in wei added on top of base fee (required for EVM chains) |

##### EVM Request Example

```json
{
  "chain": "bsc",
  "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
  "fromAddress": "0xa5e4ccf218cef628c85364253e5432d2cf18c87e",
  "toAddress": "0x2be4ccf218cef628c85364253e5432d2cf18fd21",
  "tokenAddress": "0x55d398326f99059ff775485246999027b3197955",
  "amount": "1000000000000000000",
  "extraGas": "1000000000"
}
```

##### Solana Request Example

```json
{
  "chain": "solana",
  "assetsId": "1cbac4a6674a419f88208b9f7b90cd45",
  "fromAddress": "2QfBNK2WDwSLoUQRb1zAnp3KM12N9hQ8q6ApwUMnWW2T",
  "toAddress": "BFTryQb7qro3uZaQuCMsBqXS8KNnQtWFgM3Zv3uZtF7U",
  "tokenAddress": "Fg2Z4usj7UU99XmWV7H7EYnY2LHS7jmvA1qZ9q7nbqvQ",
  "amount": "1000000000000000000",
  "gas": "10000000"
}
```

##### Response Example

```json
{
  "status": 200,
  "msg": "Success",
  "data": [
    { "id": "f50ddc7b87f04b538505cd3e6df6e78f" }
  ]
}
```

---

#### Query Transfer Status

**`GET /v1/thirdParty/tx/getTransfer?chain={chain}&ids={ids}`**

| Query Parameter | Type | Required | Description |
|----------------|------|----------|-------------|
| `chain` | string | Yes | `solana` / `bsc` / `eth` / `base` |
| `ids` | string | Yes | Comma-separated transfer order IDs |

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data[].id` | string | Order ID |
| `data[].status` | string | `generated` / `sent` / `confirmed` / `error` |
| `data[].chain` | string | Chain name |
| `data[].txHash` | string | Transaction hash |
| `data[].errorMessage` | string | Error message (if any) |

##### Response Example

```json
{
  "status": 200,
  "msg": "Success",
  "data": [
    {
      "id": "f50ddc7b87f04b538505cd3e6df6e78f",
      "status": "confirmed",
      "chain": "solana",
      "txHash": "3BP18cjNaU4xpFpTsbZ688...",
      "errorMessage": ""
    }
  ]
}
```

---

## WebSocket Push

Receive real-time notifications for proxy wallet order updates.

**URL:** `wss://bot-api.ave.ai/thirdws?ave_access_key={AVE-ACCESS-KEY}`

### Subscribe

```json
{
  "jsonrpc": "2.0",
  "method": "subscribe",
  "params": ["botswap"],
  "id": 0
}
```

### Unsubscribe

```json
{
  "jsonrpc": "2.0",
  "method": "unsubscribe",
  "params": ["botswap"],
  "id": 0
}
```

### Push Message Format

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "topic": "botswap",
    "msg": {
      "id": "f50ddc7b87f04b538505cd3e6df6e78f",
      "status": "confirmed",
      "chain": "solana",
      "assetsId": "12345678",
      "orderType": "swap",
      "swapType": "buy",
      "errorMessage": "",
      "txHash": "3BP18cjNaU4xpFpTsbZ688...",
      "autoSellTriggerHash": ""
    }
  }
}
```

### Message Fields (`result.msg`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID |
| `status` | string | `confirmed` / `error` / `auto_cancelled` |
| `chain` | string | Chain name |
| `assetsId` | string | User asset ID |
| `orderType` | string | `swap` (market order) / `limit` (limit order) |
| `swapType` | string | `buy` / `sell` / `stoploss` / `takeprofit` / `trailing` |
| `errorMessage` | string | Error message (if any) |
| `txHash` | string | Transaction hash |
| `autoSellTriggerHash` | string | Original tx hash that triggered auto-sell |

---

## Error Codes

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 4XX | Bad request — error is on the client side |
| 429 | Rate limit exceeded |

### Business Error Codes

| Code | Description |
|------|-------------|
| `200` / `0` | Success |
| `1001` | General failure |
| `1011` | System error |
| `1021` | Signature verification failed |
| `1022` | API frozen — contact customer support |
| `1023` | Request expired (timestamp out of range) |
| `2001` | Invalid request parameters |
| `3001` | Transaction submission failed |
| `3011` | Transaction record not found |
| `3021` | Order cancellation failed |
| `3101` | User not found |
| `3102` | User assets do not belong to this organization |
| `3103` | User asset account is disabled |
| `3104` | Proxy Wallet API not activated — upgrade plan to enable |

### General Notes

- All requests must include a valid signature (proxy wallet) or API key (chain wallet)
- Timestamps must be within the server's allowed time window
- POST request bodies must be valid JSON
- All token amount fields use string format (not numeric) to preserve precision

---

## Change Log

| Date | Changes |
|------|---------|
| 2026-02-28 | Chain Wallet Trading API: added Quote API |
| 2026-02-04 | Chain Wallet Trading API: added automatic slippage support |
| 2025-12-24 | Chain Wallet API: trading rebates (20% ratio), fee increased to 0.6% |
| 2025-11-14 | Proxy Wallet API: query TP/SL/trailing orders; WebSocket push for TP/SL/trailing; `AVE-ACCESS-KEY` moved from header to URL parameter in WebSocket |
| 2025-09-16 | Proxy Wallet API: auto-sell (TP/SL, trailing TP/SL); auto slippage and auto gas for market and limit orders |
| 2025-09-05 | Chain Wallet API: added API KEY verification; activation moved to cloud.ave.ai; updated pricing/rate limits |
| 2025-07-30 | Support for ETH/Base chain wallet API; ETH/Base proxy wallet market and limit trading; proxy wallet Transfer API |
| 2025-07-11 | Solana chain wallet trading API |
| 2025-07-07 | Open/delete third-party proxy wallets via API |
| 2025-06-24 | BSC chain wallet trading API |
| 2025-05-21 | Query market/limit order responses: added `inAmount` and `outAmount` fields |
| 2025-05-19 | BSC trading APIs; authorization transaction (send/query) endpoints |
| 2025-04-29 | Market and limit trading APIs launched; Solana MEV minimum gas 0.001 SOL |
