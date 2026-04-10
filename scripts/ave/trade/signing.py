"""EVM and Solana key derivation and transaction signing."""

import base64
import hashlib
import hmac
import os


def get_evm_account():
    try:
        from eth_account import Account
    except ImportError:
        raise ImportError("eth-account is required. Run: pip install eth-account>=0.10.0")
    raw_key = os.environ.get("AVE_EVM_PRIVATE_KEY")
    if raw_key:
        return Account.from_key(raw_key)
    mnemonic = os.environ.get("AVE_MNEMONIC")
    if not mnemonic:
        raise EnvironmentError("EVM signing requires AVE_EVM_PRIVATE_KEY or AVE_MNEMONIC to be set.")
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")


def get_solana_keypair():
    try:
        from solders.keypair import Keypair
    except ImportError:
        raise ImportError("solders is required. Run: pip install solders>=0.20.0")
    raw_key = os.environ.get("AVE_SOLANA_PRIVATE_KEY")
    if raw_key:
        return Keypair.from_base58_string(raw_key)
    mnemonic = os.environ.get("AVE_MNEMONIC")
    if not mnemonic:
        raise EnvironmentError("Solana signing requires AVE_SOLANA_PRIVATE_KEY or AVE_MNEMONIC to be set.")
    seed = _mnemonic_to_seed(mnemonic)
    key_bytes = _slip010_derive(seed, "m/44'/501'/0'/0'")
    return Keypair.from_seed(key_bytes)


def sign_evm_tx(tx_dict: dict, private_key) -> str:
    try:
        from eth_account import Account
    except ImportError:
        raise ImportError("eth-account is required. Run: pip install eth-account>=0.10.0")
    signed = Account.sign_transaction(tx_dict, private_key)
    return "0x" + signed.raw_transaction.hex()


def sign_solana_tx(tx_content_b64: str, keypair) -> str:
    try:
        from solders.message import MessageV0
        from solders.transaction import VersionedTransaction
    except ImportError:
        raise ImportError("solders is required. Run: pip install solders>=0.20.0")
    tx_bytes = base64.b64decode(tx_content_b64)
    msg = MessageV0.from_bytes(tx_bytes[1:])
    signed = VersionedTransaction(msg, [keypair])
    return base64.b64encode(bytes(signed)).decode()


def _mnemonic_to_seed(mnemonic: str) -> bytes:
    import unicodedata
    mnemonic_b = unicodedata.normalize("NFKD", mnemonic).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha512", mnemonic_b, b"mnemonic", 2048)


def _slip010_derive(seed: bytes, path: str) -> bytes:
    I = hmac.new(b"ed25519 seed", seed, hashlib.sha512).digest()
    key, chain_code = I[:32], I[32:]
    for comp in path.split("/")[1:]:
        hardened = comp.endswith("'")
        index = int(comp.rstrip("'"))
        if hardened:
            index += 0x80000000
        data = b"\x00" + key + index.to_bytes(4, "big")
        I = hmac.new(chain_code, data, hashlib.sha512).digest()
        key, chain_code = I[:32], I[32:]
    return key
