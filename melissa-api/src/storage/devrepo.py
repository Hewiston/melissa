import json, pathlib, uuid, time, secrets
from typing import Optional, Dict, Any, List
from .safe import validate_uuid, safe_join


ROOT = pathlib.Path(__file__).resolve().parents[2] / "storage_data"
DEV_DIR   = ROOT / "devices"
GRANTS_DIR= ROOT / "grants"
for p in (DEV_DIR, GRANTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

def _now_iso():
    import datetime as dt
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _dev_path(device_id: str) -> pathlib.Path:
    validate_uuid(device_id, "device_id")
    return safe_join(DEV_DIR, f"{device_id}.json")

def _grant_path(device_id: str) -> pathlib.Path:
    validate_uuid(device_id, "device_id")
    return safe_join(GRANTS_DIR, f"{device_id}.json")

def register_device(verification_uri: str = "http://localhost:8000/link") -> Dict[str, Any]:
    device_id = str(uuid.uuid4())
    user_code = f"{secrets.token_hex(2)}-{secrets.token_hex(2)}".upper()  # абы какой формат ABCD-1234
    rec = {
        "device_id": device_id,
        "user_id": None,
        "name": None,
        "status": "pending",  # pending|active|revoked
        "user_code": user_code,
        "user_code_expires_at": int(time.time()) + 10 * 60,
        "device_token": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "verification_uri": verification_uri
    }
    _dev_path(device_id).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    # пустые гранты
    if not _grant_path(device_id).exists():
        _grant_path(device_id).write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"device_id": device_id, "user_code": user_code, "verification_uri": verification_uri, "expires_in": 600}

def _load_device(device_id: str) -> Optional[Dict[str, Any]]:
    p = _dev_path(device_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def _save_device(doc: Dict[str, Any]) -> None:
    doc["updated_at"] = _now_iso()
    _dev_path(doc["device_id"]).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

def activate_device_by_code(user_code: str, user_id: str) -> Optional[str]:
    # поиск по файлам (MVP)
    for f in DEV_DIR.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("user_code") == user_code:
            if d.get("user_code_expires_at", 0) < int(time.time()):
                return None
            d["user_id"] = user_id
            d["status"] = "active"
            d["user_code"] = None
            d["user_code_expires_at"] = None
            # выдаём device_token
            d["device_token"] = secrets.token_urlsafe(32)
            _save_device(d)
            return d["device_id"]
    return None

def poll_device(device_id: str) -> Dict[str, Any]:
    d = _load_device(device_id)
    if not d:
        return {"error": "unknown_device"}
    if d["status"] != "active" or not d.get("device_token"):
        return {"pending": True}
    return {"device_token": d["device_token"]}

def device_by_token(device_token: str) -> Optional[Dict[str, Any]]:
    for f in DEV_DIR.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("device_token") == device_token and d.get("status") == "active":
            return d
    return None

def list_grants(device_id: str) -> List[Dict[str, Any]]:
    p = _grant_path(device_id)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))

def save_grants(device_id: str, grants: List[Dict[str, Any]]) -> None:
    _grant_path(device_id).write_text(json.dumps(grants, ensure_ascii=False, indent=2), encoding="utf-8")

def grant_strategy(device_id: str, strategy_id: str, allow_latest: bool, pinned_semver: str | None = None) -> List[Dict[str, Any]]:
    grants = list_grants(device_id)
    # заменяем, если есть
    updated = False
    for g in grants:
        if g["strategy_id"] == strategy_id:
            g["allow_latest"] = allow_latest
            g["pinned_semver"] = pinned_semver
            updated = True
            break
    if not updated:
        grants.append({"strategy_id": strategy_id, "allow_latest": allow_latest, "pinned_semver": pinned_semver})
    save_grants(device_id, grants)
    return grants
