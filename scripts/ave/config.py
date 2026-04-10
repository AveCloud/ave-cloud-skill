"""Environment variables, base URLs, plan helpers, and shared constants."""

import os

V2_BASE: str = "https://data.ave-api.xyz/v2"
WSS_BASE: str = "wss://wss.ave-api.xyz"
TRADE_BASE: str = "https://bot-api.ave.ai"
TRADE_WSS_BASE: str = "wss://bot-api.ave.ai/thirdws"

VALID_PLANS: tuple[str, ...] = ("free", "normal", "pro")
PLAN_RPS: dict[str, int] = {"free": 1, "normal": 5, "pro": 20}
PLAN_MIN_INTERVAL: dict[str, float] = {"free": 1.0, "normal": 0.2, "pro": 0.05}

RATE_LIMIT_FILE: str = "/tmp/ave_client_last_request"
TRADE_RATE_LIMIT_FILE: str = "/tmp/ave_trade_last_request"

IN_SERVER: bool = os.environ.get("AVE_IN_SERVER", "").lower() in ("1", "true", "yes")
USE_DOCKER: bool = os.environ.get("AVE_USE_DOCKER", "").lower() in ("1", "true", "yes")
SERVER_CONTAINER: str = "ave-cloud-server"
SERVER_FIFO: str = "/tmp/ave_pipe"
DOCKER_MODE_FILE: str = os.path.expanduser("~/.ave_cloud_docker_mode")

EVM_CHAINS: tuple[str, ...] = ("bsc", "eth", "base")
ALL_CHAINS: tuple[str, ...] = ("bsc", "eth", "base", "solana")
CHAIN_ID: dict[str, int] = {"bsc": 56, "eth": 1, "base": 8453}
RPC_ENV: dict[str, str] = {"bsc": "AVE_BSC_RPC_URL", "eth": "AVE_ETH_RPC_URL", "base": "AVE_BASE_RPC_URL"}
NATIVE_COIN: str = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"


def get_api_key() -> str:
    key = os.environ.get("AVE_API_KEY")
    if not key:
        raise EnvironmentError(
            "AVE_API_KEY environment variable not set. "
            "Get a free key at https://cloud.ave.ai/register | Support: https://t.me/ave_ai_cloud"
        )
    return key


def get_api_plan() -> str:
    plan = os.environ.get("API_PLAN", "free")
    if plan not in VALID_PLANS:
        raise ValueError(f"API_PLAN must be one of: {', '.join(VALID_PLANS)}")
    return plan


def get_secret_key() -> str:
    key = os.environ.get("AVE_SECRET_KEY")
    if not key:
        raise EnvironmentError(
            "AVE_SECRET_KEY environment variable not set. Required for proxy wallet operations."
        )
    return key
