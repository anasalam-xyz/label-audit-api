from typing import Literal
from pydantic import BaseModel


class ExtractedField(BaseModel):
    id: str
    label: str
    value: str
    confidence: Literal["high", "low"]


class ExtractResponse(BaseModel):
    fields: list[ExtractedField]


class CheckRequest(BaseModel):
    fields: list[ExtractedField]


class Violation(BaseModel):
    rule_code: str
    explanation: str


class CheckResponse(BaseModel):
    violations: list[Violation]
