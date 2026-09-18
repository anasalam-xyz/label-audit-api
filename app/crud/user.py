from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User
from app.models.region import Region


def _to_dict(user: User, region_name: str | None) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "role": user.role.value,
        "region": region_name,  # display name — matches UserOut's `region` field
        "region_id": user.region_id,  # internal use — dashboard/history scoping
    }


def _fetch(db: Session, **filters) -> dict | None:
    query = select(User, Region.name).outerjoin(Region, User.region_id == Region.id)
    for key, value in filters.items():
        query = query.where(getattr(User, key) == value)
    row = db.execute(query).first()
    if not row:
        return None
    user, region_name = row
    return _to_dict(user, region_name)


def authenticate(db: Session, email: str, password: str) -> dict | None:
    user = _fetch(db, email=email)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_by_id(db: Session, user_id: str) -> dict | None:
    return _fetch(db, id=user_id)
