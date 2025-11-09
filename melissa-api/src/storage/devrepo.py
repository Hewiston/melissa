import json, pathlib, time, uuid, secrets
from typing import Optional, Dict, Any, List
from .safe import validate_uuid, safe_join, validate_semver

ROOT = pathlib.Path(__file__).resolve().parents[2] / "storage_data"
DEV_DIR    = ROOT / "devices"
GRANTS_DIR = ROOT / "grants"
LINK_DIR   = ROOT / "links"

for p in (DEV_DIR, GRANTS_DIR, LINK_DIR):
    p.mkdir(parents=True, exist_ok=True)

def _dev_path(device_id: str) -> pathlib.Path:
    validate_uuid(device_id, "device_id")
    return safe_join(DEV_DIR, f"{device_id}.json")

def _grant_path(device_id: str) -> pathlib.Path:
    validate_uuid(device_id, "device_id")
    return safe_join(GRANTS_DIR, f"{device_id}.json")

def _linkcode_path(user_code: str) -> pathlib.Path:
    # user_code формат XXXX-YYYY (буквы/цифры и дефис) — без слэшей
    if not user_code or any(ch in user_code for ch in ("/", "\\", "..")):
        raise ValueError("invalid user_code")
    return safe_join(LINK_DIR, f"{user_code}.json")

def create_device_link_code() -> (str, str):
    device_id = str(uuid.uuid4())
    user_code = f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"[:9].replace("-", "")
    # Приведём к формату ABC1-DEF2
    user_code = f"{user_code[:4]}-{user_code[4:8]}"
    # сохраним заготовку девайса
    dev = {
        "device_id": device_id,
        "created_at": int(time.time()),
        "device_token": None,
        "user_id": None
    }
    _dev_path(device_id).write_text(json.dumps(dev, ensure_ascii=False, indent=2), encoding="utf-8")
    # сохраним линк-код
    link = {"device_id": device_id, "created_at": int(time.time())}
    _linkcode_path(user_code).write_text(json.dumps(link), encoding="utf-8")
    return user_code, device_id

def activate_device_by_code(user_code: str, user_id: str) -> Optional[str]:
    p = _linkcode_path(user_code)
    if not p.exists():
        return None
    link = json.loads(p.read_text(encoding="utf-8"))
    device_id = link["device_id"]
    # ttl 10 минут
    if int(time.time()) - int(link["created_at"]) > 600:
        p.unlink(missing_ok=True)
        return None
    devp = _dev_path(device_id)
    dev = json.loads(devp.read_text(encoding="utf-8"))
    if not dev.get("device_token"):
        dev["device_token"] = secrets.token_hex(16)
    dev["user_id"] = user_id
    devp.write_text(json.dumps(dev, ensure_ascii=False, indent=2), encoding="utf-8")
    p.unlink(missing_ok=True)
    return device_id

def _load_grants(device_id: str) -> Dict[str, Any]:
    gp = _grant_path(device_id)
    if not gp.exists():
        return {"device_id": device_id, "grants": []}
    return json.loads(gp.read_text(encoding="utf-8"))

def save_grant(device_id: str, strategy_id: str, allow_latest: bool, pinned_semver: Optional[str]):
    grants = _load_grants(device_id)
    # обновим/создадим
    updated = False
    for g in grants["grants"]:
        if g["strategy_id"] == strategy_id:
            g["allow_latest"]  = bool(allow_latest)
            g["pinned_semver"] = pinned_semver
            updated = True
            break
    if not updated:
        grants["grants"].append({
            "strategy_id": strategy_id,
            "allow_latest": bool(allow_latest),
            "pinned_semver": pinned_semver
        })
    _grant_path(device_id).write_text(json.dumps(grants, ensure_ascii=False, indent=2), encoding="utf-8")

def list_device_strategies(device_id: str) -> Dict[str, Any]:
    """Вернуть стратегиs с метаданными артефактов по грантам."""
    validate_uuid(device_id, "device_id")
    grants = _load_grants(device_id).get("grants", [])
    from .fsrepo import get_strategy, list_versions, read_artifact
    items: List[Dict[str, Any]] = []
    for g in grants:
        sid = g["strategy_id"]
        validate_uuid(sid, "strategy_id")
        pin = g.get("pinned_semver")
        if pin is not None:
            validate_semver(pin)
        s = get_strategy(sid)
        if not s:
            continue
        vers = list_versions(sid)
        sel = None
        if pin:
            for v in vers:
                if v["semver"] == pin:
                    sel = v
                    break
        else:
            # latest by created_at
            sel = sorted(vers, key=lambda x: x.get("created_at", 0), reverse=True)[0] if vers else None
        if not sel:
            continue
        # верни артефакт-мету
        items.append({
            "strategy_id": sid,
            "grant": g,
            "artifact": {
                "semver": sel["semver"],
                "sha256": sel["sha256"],
                "etag": sel["etag"],
                "url": f"/v1/artifacts/{sid}/{sel['semver']}"
            }
        })
    return {"device_id": device_id, "items": items}
