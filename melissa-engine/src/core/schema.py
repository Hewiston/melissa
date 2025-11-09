import json
import pathlib
from jsonschema import Draft202012Validator, exceptions as js_exc

BASE = pathlib.Path(__file__).resolve().parents[1].parents[0] / "schemas"

def _load(name: str) -> dict:
    return json.loads((BASE / f"{name}.schema.json").read_text(encoding="utf-8"))

SCHEMAS = {
    "manifest": _load("manifest"),
    "indicators": _load("indicators"),
    "rules": _load("rules"),
    "orders": _load("orders"),
}

def validate_payload_parts(payload: dict):
    try:
        Draft202012Validator(SCHEMAS["manifest"]).validate(payload["manifest"])
        Draft202012Validator(SCHEMAS["indicators"]).validate(payload["indicators"])
        Draft202012Validator(SCHEMAS["rules"]).validate(payload["rules"])
        Draft202012Validator(SCHEMAS["orders"]).validate(payload["orders"])
    except js_exc.ValidationError as e:
        path = ".".join(map(str, e.path)) if e.path else ""
        msg = f"{e.message}" + (f" (at '{path}')" if path else "")
        raise ValueError(msg) from e
