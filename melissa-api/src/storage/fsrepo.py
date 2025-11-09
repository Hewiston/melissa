import json, pathlib, time
from typing import Optional, Dict, Any, List
from .safe import validate_uuid, validate_semver, safe_join

ROOT = pathlib.Path(__file__).resolve().parents[2] / "storage_data"
STRAT_DIR = ROOT / "strategies"
ART_DIR   = ROOT / "artifacts"
for p in (STRAT_DIR, ART_DIR):
    p.mkdir(parents=True, exist_ok=True)

def _strategy_path(strategy_id: str) -> pathlib.Path:
    validate_uuid(strategy_id, "strategy_id")
    return safe_join(STRAT_DIR, f"{strategy_id}.json")

def _artifact_path(strategy_id: str, semver: str) -> pathlib.Path:
    validate_uuid(strategy_id, "strategy_id")
    validate_semver(semver)
    d = safe_join(ART_DIR, strategy_id)
    d.mkdir(parents=True, exist_ok=True)
    return safe_join(d, f"{semver}.bundle.json")

def save_strategy(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "id" not in doc:
        import uuid
        doc["id"] = str(uuid.uuid4())
        doc["created_at"] = int(time.time())
        doc["versions"] = []
    doc["updated_at"] = int(time.time())
    p = _strategy_path(doc["id"])
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc

def get_strategy(strategy_id: str) -> Optional[Dict[str, Any]]:
    p = _strategy_path(strategy_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def update_draft(strategy_id: str, draft: Dict[str, Any]):
    s = get_strategy(strategy_id)
    if not s:
        raise FileNotFoundError("strategy not found")
    s["draft"] = draft
    save_strategy(s)

def list_versions(strategy_id: str) -> List[Dict[str, Any]]:
    s = get_strategy(strategy_id)
    return s.get("versions", []) if s else []

def save_artifact(strategy_id: str, semver: str, bundle: Dict[str, Any], sha256: str, etag: str):
    ap = _artifact_path(strategy_id, semver)
    ap.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    s = get_strategy(strategy_id)
    if not s:
        raise FileNotFoundError("strategy not found")
    s.setdefault("versions", []).append({
        "semver": semver, "sha256": sha256, "etag": etag, "created_at": int(time.time())
    })
    save_strategy(s)

def read_artifact(strategy_id: str, semver: str) -> Optional[Dict[str, Any]]:
    ap = _artifact_path(strategy_id, semver)
    if not ap.exists():
        return None
    return json.loads(ap.read_text(encoding="utf-8"))
