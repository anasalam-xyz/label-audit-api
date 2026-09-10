from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.crud import history as history_crud
from app.schemas.history import HistoryResponse, ScanSummary

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
def get_history(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    scans = history_crud.list_for_user(db, user["id"])
    return HistoryResponse(scans=[ScanSummary(**s) for s in scans])
