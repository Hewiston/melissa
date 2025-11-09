import os
from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, Optional
from src.storage.devrepo import (
    create_device_link_code,
    activate_device_by_code,
    save_grant,
    list_device_strategies,
)
from src.storage.safe import validate_uuid, validate_semver

router = APIRouter()
ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN", "")

# ---------------------------
# 1) Совместимость с движком:
#    POST /v1/devices/register  → движок melissa link ожидает именно это
# ---------------------------
@router.post("/register")
def register_device() -> Dict[str, Any]:
    """
    Создаёт device + user_code. Совместимо с melissa-engine (melissa link).
    Ответ:
      { "user_code": "ABCD-1234", "device_id": "<uuid>", "link_url": "/link" }
    """
    user_code, device_id = create_device_link_code()
    return {"user_code": user_code, "device_id": device_id, "link_url": "/link"}

# ---------------------------
# 2) Вариант, который мы уже использовали через веб-форму:
#    POST /v1/devices/activate  с JSON { "user_code": "ABCD-1234" }
# ---------------------------
@router.post("/activate")
def activate(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = payload.get("user_code")
    if not code:
        raise HTTPException(status_code=422, detail="user_code is required")
    dev_id = activate_device_by_code(code, user_id="u_demo")
    if not dev_id:
        raise HTTPException(status_code=404, detail="code not found or expired")
    return {"device_id": dev_id, "status": "linked"}

# ---------------------------
# 3) Поллинг со стороны движка во время link:
#    POST /v1/devices/poll  с JSON { "device_id": "<uuid>" }
#    Ответ:
#      pending: { "status": "pending" }
#      linked : { "status": "linked", "device_id": "...", "device_token": "..." }
# ---------------------------
@router.post("/poll")
def poll(payload: Dict[str, Any]) -> Dict[str, Any]:
    device_id = payload.get("device_id")
    if not device_id:
        raise HTTPException(status_code=422, detail="device_id is required")
    validate_uuid(device_id, "device_id")

    # читаем устройство
    from src.storage.devrepo import _dev_path  # внутренний helper
    p = _dev_path(device_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="device not found")
    import json
    dev = json.loads(p.read_text(encoding="utf-8"))
    token = dev.get("device_token")
    if token:
        return {"status": "linked", "device_id": device_id, "device_token": token}
    return {"status": "pending"}

# ---------------------------
# 4) Выдать/обновить грант для устройства
#    Требует X-Admin-Token = API_ADMIN_TOKEN (если задан)
# ---------------------------
@router.post("/{device_id}/grants")
def set_grant(
    device_id: str,
    payload: Dict[str, Any],
    x_admin_token: str = Header(default=""),
):
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="admin token required")

    validate_uuid(device_id, "device_id")
    sid = payload.get("strategy_id")
    allow_latest = payload.get("allow_latest")
    pinned = payload.get("pinned_semver", None)
    if not sid or allow_latest is None:
        raise HTTPException(
            status_code=422, detail="strategy_id and allow_latest are required"
        )
    validate_uuid(sid, "strategy_id")
    if pinned is not None:
        validate_semver(pinned)

    save_grant(device_id, sid, allow_latest=bool(allow_latest), pinned_semver=pinned)
    return {"ok": True}

# ---------------------------
# 5) Список стратегий для устройства (использует Authorization: Device <token>)
# ---------------------------
@router.get("/{device_id}/strategies")
def list_for_device(device_id: str):
    validate_uuid(device_id, "device_id")
    return list_device_strategies(device_id)
