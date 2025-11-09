from fastapi import APIRouter, HTTPException, Header, Response
from src.storage.fsrepo import load_artifact_rel
from src.storage.safe import validate_uuid, validate_semver

validate_uuid(strategy_id, "strategy_id")
validate_semver(semver)

router = APIRouter()

@router.get("/{sid}/{semver}")
def get_artifact(sid: str, semver: str, if_none_match: str | None = Header(default=None, convert_underscores=False)):
    
    rel = f"{sid}/{semver}.bundle.json"
    obj = load_artifact_rel(rel)
    if not obj:
        raise HTTPException(404, "artifact not found")
    raw, etag = obj

    # Если клиент прислал If-None-Match и совпало — 304
    if if_none_match and if_none_match == etag:
        return Response(status_code=304)

    # Иначе отдать 200 + тело + ETag
    headers = {"ETag": etag, "Content-Type": "application/json; charset=utf-8"}
    return Response(content=raw, media_type="application/json", headers=headers)
