import os
import base64
from nacl.signing import SigningKey

_PRIV_B64 = os.getenv("API_ED25519_PRIVKEY_B64") or ""

def _get_signing_key() -> SigningKey:
    if not _PRIV_B64:
        raise RuntimeError("API_ED25519_PRIVKEY_B64 is not set in environment (.env)")
    return SigningKey(base64.b64decode(_PRIV_B64))

def sign_bytes(payload: bytes) -> str:
    """
    Подписывает байты Ed25519, возвращает подпись в base64.
    """
    sk = _get_signing_key()
    sig = sk.sign(payload).signature
    return base64.b64encode(sig).decode()
