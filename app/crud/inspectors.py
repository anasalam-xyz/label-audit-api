_FAKE_INSPECTORS = [
    {
        "id": "u1",
        "name": "Rakesh Kumar",
        "region": "Ranchi",
        "scans_this_week": 34,
        "violations_flagged": 6,
    },
    {
        "id": "u2",
        "name": "Anjali Verma",
        "region": "Jamshedpur",
        "scans_this_week": 28,
        "violations_flagged": 3,
    },
]


def list_for_region(db, region: str | None = None) -> list[dict]:
    return _FAKE_INSPECTORS
