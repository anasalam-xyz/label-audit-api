import json

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.gemini import extract_fields_from_image
from app.core.compliance import check_compliance
from app.core.storage import upload_photo
from app.db.session import get_db
from app.crud.scan import create_scan_with_details
from app.schemas.scan import (
    ExtractResponse,
    CheckRequest,
    CheckResponse,
    ExtractedField,
    Violation,
    SaveScanResponse,
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
    except Exception as exc:
        print(f"Extraction failed (Gemini + Groq fallback both exhausted): {exc!r}")
        raise HTTPException(502, "Extraction failed — could not read label")
    return ExtractResponse(fields=[ExtractedField(**f) for f in raw_fields])


@router.post("/check", response_model=CheckResponse)
def check(payload: CheckRequest, user: dict = Depends(get_current_user)):
    # Deterministic — no external call, so failures here are real bugs
    # (e.g. a malformed field_key), not transient/upstream issues.
    fields_dict = [f.model_dump() for f in payload.fields]
    try:
        raw_violations = check_compliance(fields_dict)
    except Exception:
        raise HTTPException(500, "Compliance check failed on the submitted fields")
    return CheckResponse(violations=[Violation(**v) for v in raw_violations])


@router.post("/save", response_model=SaveScanResponse)
async def save(
    request: Request,
    photo: UploadFile = File(...),
    fields: str = Form(...),  # JSON-encoded list[ExtractedField]-shaped dicts
    violations: str = Form(...),  # JSON-encoded list[Violation]-shaped dicts
    location_lat: float | None = Form(None),
    location_lng: float | None = Form(None),
    store_name: str | None = Form(None),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Persists the already-computed result of a scan: the original photo
    (not the preprocessed one Gemini saw — this is the record/evidence
    copy), its extracted fields, its violations, and one audit_log entry.
    Extraction and compliance-checking already happened via /extract and
    /check earlier in the flow — this endpoint doesn't repeat either.
    """
    try:
        fields_data = json.loads(fields)
        violations_data = json.loads(violations)
    except json.JSONDecodeError:
        raise HTTPException(400, "fields/violations must be valid JSON")

    image_bytes = await photo.read()
    try:
        photo_url = upload_photo(image_bytes, photo.content_type)
    except Exception as storage_exc:
        print(f"Supabase upload failed: {storage_exc}")
        raise HTTPException(502, "Photo upload failed")

    scan = create_scan_with_details(
        db,
        inspector_id=user["id"],
        photo_url=photo_url,
        fields=fields_data,
        violations=violations_data,
        location_lat=location_lat,
        location_lng=location_lng,
        store_name=store_name,
        ip_address=request.client.host if request.client else None,
    )

    return SaveScanResponse(
        id=scan.id,
        result=scan.result.value,
        scanned_at=scan.scanned_at.isoformat(),
    )
