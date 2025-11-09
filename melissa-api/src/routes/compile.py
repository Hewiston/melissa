import json
import hashlib
from fastapi import APIRouter, HTTPException
from src.services.signer import sign_bytes
from src.services.validator import validate_all

router = APIRouter()

def _canonical_bytes(payload: dict) -> bytes:
    # временно убираем hash из manifest
    manifest = payload.get("manifest", {})
    orig_hash = manifest.pop("hash", None)
    try:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    finally:
        if orig_hash is not None:
            manifest["hash"] = orig_hash
    return raw

@router.post("/")
def compile_and_sign(doc: dict):
    # ... validate_all(doc) ...
    payload = {
        "manifest": doc["manifest"], "indicators": doc["indicators"],
        "rules": doc["rules"], "orders": doc["orders"]
    }
    # считаем sha256 по каноническим байтам БЕЗ hash
    raw = _canonical_bytes(payload)
    sha = hashlib.sha256(raw).hexdigest()
    payload["manifest"]["hash"] = sha

    # подпись — по тем же каноническим байтам, НО уже с записанным hash?
    # Выбираем один путь: подписываем ТЕ ЖЕ байты, что и хэшировали (без hash)
    sig_b64 = sign_bytes(raw)  # raw без hash

    bundle = {"payload": payload, "signature_b64": sig_b64}
    # ...
    return bundle