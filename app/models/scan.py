import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Float, ForeignKey, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScanStatus(str, enum.Enum):
    draft = "draft"
    synced = "synced"


class ScanResult(str, enum.Enum):
    pass_ = "pass"
    violation = "violation"
    review = "review"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    inspector_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    # product_id (FK) intentionally omitted — the `products` table is
    # deferred (barcode prefill isn't built). Add it back when that lands.
    photo_url: Mapped[str] = mapped_column(String, nullable=False)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    store_name: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[ScanStatus] = mapped_column(
        SAEnum(ScanStatus), default=ScanStatus.draft, nullable=False
    )
    result: Mapped[ScanResult] = mapped_column(SAEnum(ScanResult), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
