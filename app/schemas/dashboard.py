from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_scans: int
    total_violations: int
    compliance_rate: int
    weekly_trend: list[int]
