import enum
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ViolationSeverity(str, enum.Enum):
    minor = "minor"
    major = "major"


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scan_id: Mapped[str] = mapped_column(
        String, ForeignKey("scans.id"), nullable=False
    )
    rule_code: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[ViolationSeverity] = mapped_column(
        SAEnum(ViolationSeverity), nullable=False
    )
    explanation: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
