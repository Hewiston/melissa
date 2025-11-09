import json
import pathlib

HOME = pathlib.Path.home() / ".melissa"
HOME.mkdir(parents=True, exist_ok=True)

DEV_FILE = HOME / "device.json"
CACHE_FILE = HOME / "cache.json"
STRAT_DIR = HOME / "strategies"
STRAT_DIR.mkdir(parents=True, exist_ok=True)

def load_device():
    if DEV_FILE.exists():
        return json.loads(DEV_FILE.read_text(encoding="utf-8"))
    return None

def save_device(obj: dict):
    DEV_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}

def save_cache(obj: dict):
    CACHE_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def bundle_path(strategy_id: str, semver: str) -> pathlib.Path:
    d = STRAT_DIR / strategy_id
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{semver}.bundle.json"
