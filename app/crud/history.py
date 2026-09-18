from datetime import date as date_type

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.scan import Scan
from app.models.extracted_field import ExtractedField


def _display_product(fields: list[ExtractedField], store_name: str | None) -> str:
    # No `products` table yet (barcode prefill is deferred), so there's no
    # real product-name lookup. Best available stand-in: the extracted
    # manufacturer text, then the store name, then a generic label.
    manufacturer = next(
        (f.extracted_value for f in fields if f.field_key == "manufacturer" and f.extracted_value),
        None,
    )
    return manufacturer or store_name or "Unlabeled Scan"


def list_for_user(db: Session, user_id: str, on_date: date_type | None = None) -> list[dict]:
    query = select(Scan).where(Scan.inspector_id == user_id)
    if on_date:
        query = query.where(func.date(Scan.scanned_at) == on_date)
    query = query.order_by(Scan.scanned_at.desc())
    scans = db.execute(query).scalars().all()

    results = []
    for scan in scans:
        # One query per scan for its fields — fine at prototype scale;
        # revisit with a join/eager-load if history grows large.
        fields = db.execute(
            select(ExtractedField).where(ExtractedField.scan_id == scan.id)
        ).scalars().all()
        results.append({
            "id": scan.id,
            "product": _display_product(fields, scan.store_name),
            "time": scan.scanned_at.strftime("%I:%M %p"),
            "scanned_at": scan.scanned_at.isoformat(),
            "status": scan.result.value,
        })
    return results
