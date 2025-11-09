import os
from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any
from src.storage.devrepo import create_device_link_code, activate_device_by_code, save_grant, list_device_strategies
from src.storage.safe import validate_uuid, validate_semver

router = APIRouter()
ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN", "")

@router.post("/link")
def link_device() -> Dict[str, Any]:
    code, device_id = create_device_link_code()
    return {"user_code": code, "device_id": device_id}

@router.post("/activate")
def activate(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = payload.get("user_code")
    if not code:
        raise HTTPException(status_code=422, detail="user_code is required")
    dev_id = activate_device_by_code(code, user_id="u_demo")
    if not dev_id:
        raise HTTPException(status_code=404, detail="code not found or expired")
    return {"device_id": dev_id, "status": "linked"}

@router.post("/{device_id}/grants")
def set_grant(device_id: str, payload: Dict[str, Any], x_admin_token: str = Header(default="")):
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="admin token required")
    validate_uuid(device_id, "device_id")
    sid = payload.get("strategy_id")
    allow_latest = payload.get("allow_latest")
    pinned = payload.get("pinned_semver", None)
    if not sid or allow_latest is None:
        raise HTTPException(status_code=422, detail="strategy_id and allow_latest are required")
    validate_uuid(sid, "strategy_id")
    if pinned is not None:
        validate_semver(pinned)
    save_grant(device_id, sid, allow_latest=bool(allow_latest), pinned_semver=pinned)
    return {"ok": True}

@router.get("/{device_id}/strategies")
def list_for_device(device_id: str):
    validate_uuid(device_id, "device_id")
    return list_device_strategies(device_id)
