from jsonschema import validate, ValidationError

REQUIRED_KEYS = ("manifest", "indicators", "rules", "orders")

# Минимальные схемы — заменишь на свои по мере развития
MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "hash": {"type": "string"},
    },
    "required": ["name"],
    "additionalProperties": True,
}

INDICATORS_SCHEMA = {"type": "array"}
RULES_SCHEMA      = {"type": "array"}
ORDERS_SCHEMA     = {"type": "object"}

def validate_all(doc: dict):
    missing = [k for k in REQUIRED_KEYS if k not in doc]
    if missing:
        raise ValueError(f"Missing top-level sections: {', '.join(missing)}")
    try:
        validate(doc["manifest"],   MANIFEST_SCHEMA)
        validate(doc["indicators"], INDICATORS_SCHEMA)
        validate(doc["rules"],      RULES_SCHEMA)
        validate(doc["orders"],     ORDERS_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"Schema validation error: {e.message}")
