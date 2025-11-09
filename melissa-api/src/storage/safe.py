import pathlib
import re
from fastapi import HTTPException

UUID_RE   = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")

def validate_uuid(uid: str, what: str):
    if not UUID_RE.match(uid or ""):
        raise HTTPException(status_code=422, detail=f"Invalid {what} format")

def validate_semver(ver: str):
    if not SEMVER_RE.match(ver or ""):
        raise HTTPException(status_code=422, detail="Invalid semver")

def ensure_no_separators(s: str, what: str):
    if any(ch in s for ch in ("/", "\\", "..")):
        raise HTTPException(status_code=422, detail=f"Invalid {what}")

def safe_join(root: pathlib.Path, *parts: str) -> pathlib.Path:
    # запретить разделители в частях и нормализовать
    for i, p in enumerate(parts):
        ensure_no_separators(p, f"path segment {i}")
    p = (root / pathlib.Path(*parts)).resolve()
    root = root.resolve()
    if not str(p).startswith(str(root) + "\\") and str(p) != str(root):
        # на *nix добавь '/' вместо '\\'
        if not str(p).startswith(str(root) + "/") and str(p) != str(root):
            raise HTTPException(status_code=400, detail="Path outside of storage root")
    return p
