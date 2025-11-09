from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from src.storage.fsrepo import (
    create_strategy, list_strategies, get_strategy, update_draft, save_artifact
)
from src.services.validator import validate_all
from src.services.signer import sign_bytes
import json
import hashlib

router = APIRouter()

def _demo_user() -> str:
    # до реальной авторизации просто возвращаем демо-юзера
    return "u_demo"

@router.get("/")
def list_my_strategies():
    return list_strategies(_demo_user())

@router.post("/")
def create_new_strategy(payload: Dict[str, Any]):
    name = payload.get("name")
    if not name:
        raise HTTPException(422, "name is required")
    return create_strategy(_demo_user(), name)

@router.get("/{sid}")
def get_strategy_by_id(sid: str):
    s = get_strategy(sid)
    if not s:
        raise HTTPException(404, "not found")
    if s["user_id"] != _demo_user():
        raise HTTPException(403, "forbidden")
    return s

@router.put("/{sid}/draft")
def put_draft(sid: str, draft: Dict[str, Any]):
    # валидация по схемам
    try:
        validate_all(draft)
    except ValueError as ve:
        raise HTTPException(422, f"schema: {ve}") from ve
    s = get_strategy(sid)
    if not s:
        raise HTTPException(404, "not found")
    if s["user_id"] != _demo_user():
        raise HTTPException(403, "forbidden")
    return update_draft(sid, draft)

@router.post("/{sid}/publish")
def publish_version(sid: str, body: Dict[str, Any]):
    """
    body: { "semver": "1.0.0" }
    Собирает payload из draft, добавляет manifest.hash, подписывает, сохраняет bundle на диск,
    возвращает meta (artifact url позже, сейчас отдаем относительный путь).
    """
    semver = body.get("semver")
    if not semver:
        raise HTTPException(422, "semver is required")

    s = get_strategy(sid)
    if not s:
        raise HTTPException(404, "not found")
    if s["user_id"] != _demo_user():
        raise HTTPException(403, "forbidden")
    if not s.get("draft"):
        raise HTTPException(400, "draft is empty")

    draft = s["draft"]
    # повторная валидация
    try:
        validate_all(draft)
    except ValueError as ve:
        raise HTTPException(422, f"schema: {ve}") from ve

    payload = {
        "manifest": draft["manifest"],
        "indicators": draft["indicators"],
        "rules": draft["rules"],
        "orders": draft["orders"],
    }
    if "policy" in draft and draft["policy"] is not None:
        payload["policy"] = draft["policy"]

    # первичный raw и sha
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sha = hashlib.sha256(raw).hexdigest()
    payload["manifest"]["hash"] = sha
    payload["manifest"]["signature_alg"] = "ed25519"

    # финальный raw и подпись
    raw2 = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig_b64 = sign_bytes(raw2)

    bundle = {"payload": payload, "signature": {"alg":"ed25519","sig_b64": sig_b64}}
    meta = save_artifact(sid, semver, bundle)

    # относительный URL артефакта для нашего GET /v1/artifacts/{sid}/{semver}
    return {
        "strategy_id": sid,
        "semver": semver,
        "artifact_path": f"{sid}/{semver}.bundle.json",
        "sha256": meta["sha256"],
        "etag": meta["etag"],
        "sig_b64": sig_b64
    }
