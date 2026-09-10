from pydantic import BaseModel


class InspectorOut(BaseModel):
    id: str
    name: str
    region: str
    scans_this_week: int
    violations_flagged: int


class InspectorListResponse(BaseModel):
    inspectors: list[InspectorOut]
