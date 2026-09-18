from sqlalchemy.orm import Session

from app.models.scan import Scan, ScanStatus, ScanResult
from app.models.extracted_field import ExtractedField as ExtractedFieldModel
from app.models.violation import Violation as ViolationModel
from app.models.audit_log import AuditLog


def _compute_result(violations: list[dict], fields: list[dict]) -> ScanResult:
    """
    Single source of truth for the persisted pass/violation/review verdict.

    IMPORTANT: if ResultStep on the frontend computes this independently
    for the in-session display, that logic and this logic must agree —
    otherwise a scan can show one result live and a different one once
    it's read back from history/dashboard. Verify parity; align whichever
    side is wrong.
    """
    if any(v["severity"] == "major" for v in violations):
        return ScanResult.violation
    if any(v["severity"] == "minor" for v in violations):
        return ScanResult.review
    if any(f["confidence"] == "low" for f in fields):
        return ScanResult.review
    return ScanResult.pass_


def create_scan_with_details(
    db: Session,
    *,
    inspector_id: str,
    photo_url: str,
    fields: list[dict],
    violations: list[dict],
    location_lat: float | None,
    location_lng: float | None,
    store_name: str | None,
    ip_address: str | None,
) -> Scan:
    """
    Persist a completed scan: the scan row itself, its extracted fields,
    its violations, and a single audit_log entry — as one transaction.
    `db` accepted and actually used now (this was previously a no-op
    seam in the fake crud layer — this is the real implementation).
    """
    result = _compute_result(violations, fields)

    scan = Scan(
        inspector_id=inspector_id,
        photo_url=photo_url,
        location_lat=location_lat,
        location_lng=location_lng,
        store_name=store_name,
        status=ScanStatus.synced,
        result=result,
    )
    db.add(scan)
    db.flush()  # populates scan.id without committing yet

    for f in fields:
        db.add(ExtractedFieldModel(
            scan_id=scan.id,
            field_key=f["field_key"],
            extracted_value=f["value"],
            confidence=f["confidence"],
            manually_corrected=f.get("manually_corrected", False),
            corrected_value=f.get("corrected_value"),
        ))

    for v in violations:
        db.add(ViolationModel(
            scan_id=scan.id,
            rule_code=v["rule_code"],
            severity=v["severity"],
            explanation=v["explanation"],
        ))

    db.add(AuditLog(
        user_id=inspector_id,
        action="scan_saved",
        entity_type="scan",
        entity_id=scan.id,
        ip_address=ip_address,
    ))

    db.commit()
    db.refresh(scan)
    return scan
