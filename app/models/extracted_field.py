import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FieldConfidence(str, enum.Enum):
    high = "high"
    low = "low"


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scan_id: Mapped[str] = mapped_column(
        String, ForeignKey("scans.id"), nullable=False
    )
    # Renamed from the original plan's field_name to field_key — matches
    # the stable identifier core/compliance.py matches rules against
    # (manufacturer / net_quantity / mfg_date / mrp / consumer_care).
    field_key: Mapped[str] = mapped_column(String, nullable=False)
    extracted_value: Mapped[str] = mapped_column(String, nullable=False)
    # Categorical, not numeric — matches what Gemini actually returns
    # and what ReviewStep already renders.
    confidence: Mapped[FieldConfidence] = mapped_column(
        SAEnum(FieldConfidence), nullable=False
    )
    manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_value: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
