from typing import Literal
from pydantic import BaseModel


class ScanSummary(BaseModel):
    id: str
    product: str
    time: str
    status: Literal["pass", "violation", "review"]


class HistoryResponse(BaseModel):
    scans: list[ScanSummary]
