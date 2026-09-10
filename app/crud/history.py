_FAKE_HISTORY = [
    {"id": "1", "product": "Tata Salt 1kg", "time": "10:42 AM", "status": "pass"},
    {
        "id": "2",
        "product": "Local Brand Atta 5kg",
        "time": "10:15 AM",
        "status": "violation",
    },
    {"id": "3", "product": "Amul Butter 500g", "time": "9:58 AM", "status": "pass"},
]


def list_for_user(db, user_id: str) -> list[dict]:
    return _FAKE_HISTORY
