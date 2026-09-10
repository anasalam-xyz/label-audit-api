from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_role
from app.crud import inspectors as inspector_crud
from app.schemas.inspector import InspectorListResponse, InspectorOut

router = APIRouter(prefix="/inspectors", tags=["inspectors"])


@router.get("", response_model=InspectorListResponse)
def list_inspectors(
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("supervisor", "admin")),
):
    inspectors = inspector_crud.list_for_region(db, region=user.get("region"))
    return InspectorListResponse(inspectors=[InspectorOut(**i) for i in inspectors])
