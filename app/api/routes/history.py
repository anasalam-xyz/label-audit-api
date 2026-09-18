from datetime import date as date_type

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.crud import history as history_crud
from app.schemas.history import HistoryResponse, ScanSummary

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
def get_history(
    date: date_type | None = Query(None, description="Filter to scans on this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scans = history_crud.list_for_user(db, user["id"], on_date=date)
    return HistoryResponse(scans=[ScanSummary(**s) for s in scans])
