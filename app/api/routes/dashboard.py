from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_role
from app.crud import dashboard as dashboard_crud
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("supervisor", "admin")),
):
    # region_id, not region: filtering needs the FK, display uses the name.
    stats = dashboard_crud.get_stats(db, region_id=user.get("region_id"))
    return DashboardResponse(**stats)
