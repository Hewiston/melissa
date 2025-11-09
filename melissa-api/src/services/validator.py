import json
import pathlib
from jsonschema import Draft202012Validator, exceptions as js_exc

BASE = pathlib.Path(__file__).resolve().parents[1] / "schemas"

SCHEMAS = {
    "manifest": json.loads((BASE / "manifest.schema.json").read_text(encoding="utf-8")),
    "indicators": json.loads((BASE / "indicators.schema.json").read_text(encoding="utf-8")),
    "rules": json.loads((BASE / "rules.schema.json").read_text(encoding="utf-8")),
    "orders": json.loads((BASE / "orders.schema.json").read_text(encoding="utf-8")),
}

def validate_part(name: str, doc: dict):
    schema = SCHEMAS[name]
    Draft202012Validator(schema).validate(doc)

def validate_all(doc: dict):
    try:
        validate_part("manifest", doc["manifest"])
        validate_part("indicators", doc["indicators"])
        validate_part("rules", doc["rules"])
        validate_part("orders", doc["orders"])
    except js_exc.ValidationError as e:
        # сделаем читабельную ошибку
        path = ".".join(map(str, e.path)) if e.path else ""
        msg = f"{e.message}" + (f" (at '{path}')" if path else "")
        raise ValueError(msg) from e
