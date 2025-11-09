import base64
import json
import hashlib
from nacl.signing import VerifyKey

def verify_bundle(bundle: dict, public_key_b64: str) -> None:
    # 1) проверяем, что структура есть
    if "payload" not in bundle or "signature" not in bundle:
        raise ValueError("Invalid bundle structure")

    payload = bundle["payload"]
    sig_b64 = bundle["signature"].get("sig_b64")
    alg = bundle["signature"].get("alg")

    if alg != "ed25519":
        raise ValueError("Unsupported signature alg")

    # 2) сериализуем payload строго
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()

    # 3) сверка sha256
    sha = hashlib.sha256(raw).hexdigest()
    mhash = payload.get("manifest", {}).get("hash")
    if sha != mhash:
        raise ValueError(f"Hash mismatch: calc={sha}, manifest={mhash}")

    # 4) верификация подписи
    vk = VerifyKey(base64.b64decode(public_key_b64))
    vk.verify(raw, base64.b64decode(sig_b64))  # бросит исключение при неверной подписи
