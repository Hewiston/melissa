from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from src.storage.fsrepo import get_strategy, save_strategy, update_draft, list_versions, save_artifact
from src.storage.safe import validate_uuid, validate_semver
from src.services.validator import validate_all
from src.routes.compile import canonical_bytes, sign_payload_and_hash  # используем общую логику хэша/подписи

router = APIRouter()

@router.post("")
def create_strategy(body: Dict[str, Any]):
    name = (body or {}).get("name") or "Untitled"
    doc = save_strategy({"name": name})
    return doc

@router.get("/{sid}")
def get_by_id(sid: str):
    validate_uuid(sid, "strategy_id")
    s = get_strategy(sid)
    if not s:
        raise HTTPException(status_code=404, detail="not found")
    return s

@router.put("/{sid}/draft")
def put_draft(sid: str, body: Dict[str, Any]):
    validate_uuid(sid, "strategy_id")
    try:
        validate_all(body)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    update_draft(sid, body)
    return {"ok": True}

@router.post("/{sid}/publish")
def publish(sid: str, req: Dict[str, Any]):
    validate_uuid(sid, "strategy_id")
    semver = (req or {}).get("semver")
    if not semver:
        raise HTTPException(status_code=422, detail="semver is required")
    validate_semver(semver)
    if any(v["semver"] == semver for v in list_versions(sid)):
        raise HTTPException(status_code=409, detail="Version already exists; use a new semver")

    s = get_strategy(sid)
    if not s or not s.get("draft"):
        raise HTTPException(status_code=400, detail="no draft to publish")

    payload = s["draft"]
    # считаем канонические байты (без manifest.hash), получаем sha и подпись
    raw, sha_hex, signature_obj = sign_payload_and_hash(payload)
    etag = f'W/"{sha_hex}"'

    # сохраняем файл артефакта + мету версии
    save_artifact(sid, semver, {"payload": payload, "signature": signature_obj}, sha256=sha_hex, etag=etag)
    return {"semver": semver, "sha256": sha_hex, "etag": etag}
