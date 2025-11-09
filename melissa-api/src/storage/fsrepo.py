import json
import os
import pathlib
import time
import hashlib
from typing import Any, Dict, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2] / "storage_data"
STRATS_DIR = ROOT / "strategies"
ART_DIR = ROOT / "artifacts"

for p in (STRATS_DIR, ART_DIR):
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

def get_strategy(sid: str) -> Optional[Dict[str, Any]]:
    p = STRATS_DIR / f"{sid}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def update_draft(sid: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    cur = get_strategy(sid)
    if not cur:
        raise FileNotFoundError("strategy not found")
    cur["draft"] = draft
    cur["updated_at"] = _now_iso()
    (STRATS_DIR / f"{sid}.json").write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur

def save_artifact(sid: str, semver: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
    # bundle -> bytes (minified)
    raw = json.dumps(bundle, separators=(",", ":"), ensure_ascii=False).encode()
    sha = hashlib.sha256(raw).hexdigest()
    etag = f'W/"{sha}"'

    # путь артефакта
    base = ART_DIR / sid
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{semver}.bundle.json"
    path.write_text(raw.decode("utf-8"), encoding="utf-8")

    # обновить карточку стратегии
    cur = get_strategy(sid)
    if not cur:
        raise FileNotFoundError("strategy not found")
    # не дублировать запись
    if not any(v["semver"] == semver for v in cur["versions"]):
        cur["versions"].append({
            "semver": semver,
            "sha256": sha,
            "etag": etag,
            "created_at": _now_iso()
        })
        cur["updated_at"] = _now_iso()
        (STRATS_DIR / f"{sid}.json").write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")

    # meta для ответа
    return {
        "sha256": sha,
        "etag": etag,
        "artifact_rel": f"{sid}/{semver}.bundle.json"
    }

def load_artifact_rel(rel_path: str) -> Optional[tuple[bytes, str]]:
    p = ART_DIR / rel_path
    if not p.exists():
        return None
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    etag = f'W/"{sha}"'
    return raw, etag
