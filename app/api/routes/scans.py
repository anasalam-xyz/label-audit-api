from fastapi import APIRouter, Depends, File, UploadFile, HTTPException

from app.api.deps import get_current_user
from app.core.gemini import extract_fields_from_image, check_compliance
from app.schemas.scan import (
    ExtractResponse,
    CheckRequest,
    CheckResponse,
    ExtractedField,
    Violation,
)

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    photo: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    image_bytes = await photo.read()
    try:
        raw_fields = extract_fields_from_image(image_bytes, photo.content_type)
    except Exception:
        raise HTTPException(502, "Extraction failed — could not read label")
    return ExtractResponse(fields=[ExtractedField(**f) for f in raw_fields])


@router.post("/check", response_model=CheckResponse)
def check(payload: CheckRequest, user: dict = Depends(get_current_user)):
    fields_dict = [f.model_dump() for f in payload.fields]
    try:
        raw_violations = check_compliance(fields_dict)
    except Exception:
        raise HTTPException(502, "Compliance check failed")
    return CheckResponse(violations=[Violation(**v) for v in raw_violations])
