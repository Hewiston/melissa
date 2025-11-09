from fastapi import APIRouter, HTTPException
from src.storage.fsrepo import read_artifact
from src.storage.safe import validate_uuid, validate_semver

router = APIRouter()

@router.get("/{strategy_id}/{semver}")
def get_artifact(strategy_id: str, semver: str):
    validate_uuid(strategy_id, "strategy_id")
    validate_semver(semver)
    bundle = read_artifact(strategy_id, semver)
    if not bundle:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return bundle
