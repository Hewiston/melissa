from fastapi import APIRouter, HTTPException, Header, Body
from typing import Dict, Any, Optional
from src.storage.devrepo import (
    register_device, activate_device_by_code, poll_device, device_by_token, grant_strategy, list_grants
)
from src.storage.fsrepo import get_strategy

router = APIRouter()

def _demo_user() -> str:
    return "u_demo"

@router.post("/register")
def register():
    return register_device(verification_uri="http://localhost:8000/link")

@router.post("/activate")
def activate(payload: Dict[str, Any]):
    """
    Тело: { "user_code": "ABCD-1234" }
    Подразумеваем, что вызывается от имени пользователя (MVP без auth: демо-пользователь).
    """
    code = payload.get("user_code")
    if not code:
        raise HTTPException(422, "user_code required")
    dev_id = activate_device_by_code(code, _demo_user())
    if not dev_id:
        raise HTTPException(400, "invalid_or_expired_code")
    return {"device_id": dev_id, "status": "linked"}

@router.post("/poll")
def poll(payload: Dict[str, Any]):
    """
    Тело: { "device_id": "uuid" }
    Возвращает {pending:true} пока не активировано
    После активации -> {device_token:"..."} (сохраняй на движке)
    """
    dev_id = payload.get("device_id")
    if not dev_id:
        raise HTTPException(422, "device_id required")
    return poll_device(dev_id)

@router.post("/{device_id}/grants")
def set_grant(device_id: str, payload: Dict[str, Any]):
    """
    Тело: { "strategy_id":"...", "allow_latest":true, "pinned_semver":null }
    Выдаёт устройству доступ к стратегии.
    """
    sid = payload.get("strategy_id")
    allow_latest = payload.get("allow_latest")
    pinned = payload.get("pinned_semver")
    if sid is None or allow_latest is None:
        raise HTTPException(422, "strategy_id and allow_latest required")
    # проверим, что стратегия существует и принадлежит демо-юзеру (MVP)
    s = get_strategy(sid)
    if not s:
        raise HTTPException(404, "strategy not found")
    # записываем грант
    grants = grant_strategy(device_id, sid, bool(allow_latest), pinned)
    return {"ok": True, "grants": grants}

@router.get("/{device_id}/strategies")
def list_for_device(device_id: str, authorization: Optional[str] = Header(default=None)):
    """
    Заголовок: Authorization: Device <token>
    Отдаёт список стратегий, доступных устройству, с указанием latest/pinned и артефакта.
    Для MVP: latest = последняя опубликованная версия в списке.
    """
    # валидация токена
    if not authorization or not authorization.startswith("Device "):
        raise HTTPException(401, "missing device token")
    token = authorization.split(" ", 1)[1].strip()
    dev = device_by_token(token)
    if not dev or dev.get("device_id") != device_id:
        raise HTTPException(401, "invalid device token")

    # соберём список грантов
    grants = list_grants(device_id)
    out = []
    for g in grants:
        sid = g["strategy_id"]
        s = get_strategy(sid)
        if not s:
            continue
        # latest = последняя версия по created_at
        versions = s.get("versions", [])
        if not versions:
            continue
        latest = sorted(versions, key=lambda v: v["created_at"])[-1]["semver"]
        chosen = g["pinned_semver"] or (latest if g["allow_latest"] else None)
        art = None
        if chosen:
            # артефакт доступен по GET /v1/artifacts/{sid}/{chosen}
            # ETag при скачивании: W/"<sha256>"
            # sha256 берём из карточки версии
            vmeta = next((v for v in versions if v["semver"] == chosen), None)
            if vmeta:
                art = {
                    "semver": chosen,
                    "url": f"/v1/artifacts/{sid}/{chosen}",
                    "sha256": vmeta["sha256"],
                    "etag": vmeta["etag"]
                }
        out.append({
            "strategy_id": sid,
            "name": s["name"],
            "latest": latest,
            "pinned": g["pinned_semver"],
            "allow_latest": g["allow_latest"],
            "artifact": art
        })
    return out
