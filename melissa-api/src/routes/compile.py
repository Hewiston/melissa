import json
import hashlib
from fastapi import APIRouter, HTTPException
from src.services.signer import sign_bytes
from src.services.validator import validate_all

router = APIRouter()

@router.post("/")
def compile_and_sign(doc: dict):
    required = ["manifest", "indicators", "rules", "orders"]
    for k in required:
        if k not in doc:
            raise HTTPException(422, f"missing: {k}")

    # 1) валидация
    try:
        validate_all(doc)
    except ValueError as ve:
        raise HTTPException(422, f"schema: {ve}") from ve

    # 2) сборка и подпись
    payload = {
        "manifest": doc["manifest"],
        "indicators": doc["indicators"],
        "rules": doc["rules"],
        "orders": doc["orders"],
    }
    if "policy" in doc and doc["policy"] is not None:
        payload["policy"] = doc["policy"]

    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sha = hashlib.sha256(raw).hexdigest()
    payload["manifest"]["hash"] = sha
    payload["manifest"]["signature_alg"] = "ed25519"
    raw2 = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig_b64 = sign_bytes(raw2)

    return {"payload": payload, "signature": {"alg": "ed25519", "sig_b64": sig_b64}}
