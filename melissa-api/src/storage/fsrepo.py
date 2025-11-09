import json, pathlib, hashlib, time
import os
from typing import Optional, Dict, Any, List
from .safe import validate_uuid, validate_semver, safe_join



ROOT = pathlib.Path(__file__).resolve().parents[2] / "storage_data"
STRAT_DIR = ROOT / "strategies"
ART_DIR   = ROOT / "artifacts"
for p in (STRAT_DIR, ART_DIR):
    p.mkdir(parents=True, exist_ok=True)



def _now_iso():
    import datetime as dt
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _sid_exists(sid: str) -> bool:
    return (STRATS_DIR / f"{sid}.json").exists()

def create_strategy(user_id: str, name: str) -> Dict[str, Any]:
    import uuid
    sid = str(uuid.uuid4())
    doc = {
        "id": sid,
        "user_id": user_id,
        "name": name,
        "draft": None,        # сюда будем класть {manifest, indicators, rules, orders, policy?}
        "versions": [],       # список {semver, sha256, etag, created_at}
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    (STRATS_DIR / f"{sid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc

def list_strategies(user_id: str) -> list[Dict[str, Any]]:
    out = []
    for f in STRATS_DIR.glob("*.json"):
        j = json.loads(f.read_text(encoding="utf-8"))
        if j.get("user_id") == user_id:
            out.append(j)
    return out


def _strategy_path(strategy_id: str) -> pathlib.Path:
    validate_uuid(strategy_id, "strategy_id")
    return safe_join(STRAT_DIR, f"{strategy_id}.json")

def _artifact_path(strategy_id: str, semver: str) -> pathlib.Path:
    validate_uuid(strategy_id, "strategy_id")
    validate_semver(semver)
    d = safe_join(ART_DIR, strategy_id)
    d.mkdir(parents=True, exist_ok=True)
    return safe_join(d, f"{semver}.bundle.json")


def get_strategy(strategy_id: str) -> Optional[Dict[str, Any]]:
    p = _strategy_path(strategy_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_strategy(doc: Dict[str, Any]) -> None:
    p = _strategy_path(doc["id"])
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def list_versions(strategy_id: str) -> List[Dict[str, Any]]:
    s = get_strategy(strategy_id)
    if not s:
        return []
    return s.get("versions", [])


def update_draft(sid: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    cur = get_strategy(sid)
    if not cur:
        raise FileNotFoundError("strategy not found")
    cur["draft"] = draft
    cur["updated_at"] = _now_iso()
    (STRATS_DIR / f"{sid}.json").write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur

def save_artifact(strategy_id: str, semver: str, bundle: Dict[str, Any], sha256: str, etag: str) -> Dict[str, Any]:
    # политика: запрещаем дубликаты semver → 409 handled в роутере
    ap = _artifact_path(strategy_id, semver)
    ap.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    s = get_strategy(strategy_id)
    assert s, "strategy must exist"
    if any(v["semver"] == semver for v in s.get("versions", [])):
        # не обновляем мету здесь — роутер решает: либо 409, либо обновление записи
        return {"already_exists": True}
    s.setdefault("versions", []).append({
        "semver": semver, "sha256": sha256, "etag": etag, "created_at": int(time.time())
    })
    save_strategy(s)
    return {"already_exists": False}

def read_artifact(strategy_id: str, semver: str) -> Optional[Dict[str, Any]]:
    ap = _artifact_path(strategy_id, semver)
    if not ap.exists():
        return None
    return json.loads(ap.read_text(encoding="utf-8"))

def load_artifact_rel(rel_path: str) -> Optional[tuple[bytes, str]]:
    p = ART_DIR / rel_path
    if not p.exists():
        return None
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    etag = f'W/"{sha}"'
    return raw, etag
