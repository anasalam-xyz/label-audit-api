def get_stats(db, region: str | None = None) -> dict:
    return {
        "total_scans": 214,
        "total_violations": 37,
        "compliance_rate": 83,
        "weekly_trend": [12, 18, 15, 22, 19, 25, 20],
    }
