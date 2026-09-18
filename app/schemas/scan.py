from typing import Literal
from pydantic import BaseModel


class ExtractedField(BaseModel):
    id: str
    field_key: str  # stable key for rule matching — see core/compliance.py
    label: str
    value: str
    confidence: Literal["high", "low"]


class ExtractResponse(BaseModel):
    fields: list[ExtractedField]


class CheckRequest(BaseModel):
    fields: list[ExtractedField]


class Violation(BaseModel):
    rule_code: str
    severity: Literal["minor", "major"]
    explanation: str


class CheckResponse(BaseModel):
    violations: list[Violation]


class SaveScanResponse(BaseModel):
    id: str
    result: Literal["pass", "violation", "review"]
    scanned_at: str
