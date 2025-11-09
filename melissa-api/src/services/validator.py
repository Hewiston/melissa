import json
import pathlib
from jsonschema import Draft202012Validator, exceptions as js_exc
from jsonschema import validate, ValidationError


BASE = pathlib.Path(__file__).resolve().parents[1] / "schemas"
REQUIRED_KEYS = ("manifest","indicators","rules","orders")

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
    # 1) ключи
    missing = [k for k in REQUIRED_KEYS if k not in doc]
    if missing:
        raise ValueError(f"Missing top-level sections: {', '.join(missing)}")
    # 2) далее — jsonschema.validate(...) для каждой секции/целого документа
    try:
        # validate(doc, FULL_SCHEMA)  # если есть общая схема
        pass
    except ValidationError as e:
        raise ValueError(f"Schema validation error: {e.message}")