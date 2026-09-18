from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.scan import Scan, ScanResult
from app.models.user import User
from app.models.violation import Violation


def get_stats(db: Session, region_id: str | None = None) -> dict:
    inspector_ids_query = select(User.id).where(User.role == "inspector")
    if region_id:
        inspector_ids_query = inspector_ids_query.where(User.region_id == region_id)
    inspector_ids = [row[0] for row in db.execute(inspector_ids_query).all()]

    if not inspector_ids:
        return {
            "total_scans": 0,
            "total_violations": 0,
            "compliance_rate": 0,
            "weekly_trend": [0] * 7,
        }

    total_scans = db.execute(
        select(func.count(Scan.id)).where(Scan.inspector_id.in_(inspector_ids))
    ).scalar_one()

    total_violations = db.execute(
        select(func.count(Violation.id))
        .join(Scan, Violation.scan_id == Scan.id)
        .where(Scan.inspector_id.in_(inspector_ids))
    ).scalar_one()

    passed = db.execute(
        select(func.count(Scan.id)).where(
            Scan.inspector_id.in_(inspector_ids),
            Scan.result == ScanResult.pass_,
        )
    ).scalar_one()
    compliance_rate = round((passed / total_scans) * 100) if total_scans else 0

    today = date.today()
    weekly_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.execute(
            select(func.count(Scan.id)).where(
                Scan.inspector_id.in_(inspector_ids),
                func.date(Scan.scanned_at) == day,
            )
        ).scalar_one()
        weekly_trend.append(count)

    return {
        "total_scans": total_scans,
        "total_violations": total_violations,
        "compliance_rate": compliance_rate,
        "weekly_trend": weekly_trend,
    }
