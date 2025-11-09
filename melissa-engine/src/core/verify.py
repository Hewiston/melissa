import base64
import json
import hashlib
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def _canonical_bytes(payload: dict) -> bytes:
    # исключаем manifest.hash перед сериализацией
    manifest = payload.get("manifest", {})
    orig_hash = manifest.pop("hash", None)
    try:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    finally:
        if orig_hash is not None:
            manifest["hash"] = orig_hash

def verify_bundle(bundle: dict, pubkey_b64: str):
    payload = bundle["payload"]
    sig_b64 = bundle["signature_b64"]

    raw = _canonical_bytes(payload)
    sha = hashlib.sha256(raw).hexdigest()
    if payload.get("manifest", {}).get("hash") != sha:
        raise ValueError("Hash mismatch")

    vk = VerifyKey(base64.b64decode(pubkey_b64))
    try:
        vk.verify(raw, base64.b64decode(sig_b64))
    except BadSignatureError:
        raise ValueError("Signature mismatch")