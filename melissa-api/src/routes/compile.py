import json, hashlib
from fastapi import APIRouter, HTTPException
from src.services.validator import validate_all
from src.services.signer import sign_bytes

router = APIRouter()

def canonical_bytes(payload: dict) -> bytes:
    # сериализация без manifest.hash
    manifest = payload.get("manifest", {})
    orig_hash = manifest.pop("hash", None)
    try:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    finally:
        if orig_hash is not None:
            manifest["hash"] = orig_hash

def sign_payload_and_hash(payload: dict):
    raw = canonical_bytes(payload)
    sha_hex = hashlib.sha256(raw).hexdigest()
    payload.setdefault("manifest", {})["hash"] = sha_hex
    sig_b64 = sign_bytes(raw)
    signature = {"alg": "ed25519+sha256(canonical,no-hash)", "sig_b64": sig_b64}
    return raw, sha_hex, signature

@router.post("/")
def compile_and_sign(doc: dict):
    try:
        validate_all(doc)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    payload = {
        "manifest": doc["manifest"],
        "indicators": doc["indicators"],
        "rules": doc["rules"],
        "orders": doc["orders"],
    }
    _, _, signature = sign_payload_and_hash(payload)
    return {"payload": payload, "signature": signature}
