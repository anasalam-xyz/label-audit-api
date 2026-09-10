from app.core.security import hash_password, verify_password

# Fake user store. `db` is accepted (and ignored) in every function so the
# signature already matches what a real `db: Session` query needs — the
# route file below never has to change when this becomes a real lookup.
_FAKE_USERS = [
    {
        "id": "u1",
        "name": "Rakesh Kumar",
        "email": "rakesh@labelaudit.gov.in",
        "hashed_password": hash_password("inspector123"),
        "role": "inspector",
        "region": "Ranchi",
    },
    {
        "id": "u2",
        "name": "Anjali Verma",
        "email": "anjali@labelaudit.gov.in",
        "hashed_password": hash_password("inspector123"),
        "role": "inspector",
        "region": "Jamshedpur",
    },
    {
        "id": "u3",
        "name": "Suresh Prasad",
        "email": "suresh@labelaudit.gov.in",
        "hashed_password": hash_password("supervisor123"),
        "role": "supervisor",
        "region": "Ranchi",
    },
]


def authenticate(db, email: str, password: str) -> dict | None:
    user = next((u for u in _FAKE_USERS if u["email"] == email), None)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_by_id(db, user_id: str) -> dict | None:
    return next((u for u in _FAKE_USERS if u["id"] == user_id), None)
