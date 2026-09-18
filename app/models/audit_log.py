import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """
    Scoped intentionally narrow: one INSERT from the scan-save handler,
    not general request middleware. Extend later if broader coverage
    is worth the effort — not needed for the current pitch/demo scope.
    """

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "scan_saved"
    entity_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "scan"
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
