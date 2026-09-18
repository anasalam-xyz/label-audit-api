import uuid

import httpx

from app.core.config import settings

_EXTENSION_BY_MIME = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def upload_photo(image_bytes: bytes, content_type: str) -> str:
    """
    Upload a scan photo to Supabase Storage and return its public URL.
    Uses a plain httpx call against the Storage REST API rather than the
    supabase-py client, to avoid pulling in another dependency tree on a
    RAM-constrained (512MB) Render free-tier deploy.
    """
    ext = _EXTENSION_BY_MIME.get(content_type, "jpg")
    filename = f"{uuid.uuid4()}.{ext}"

    upload_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/"
        f"{settings.SUPABASE_BUCKET}/{filename}"
    )
    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": content_type,
    }

    response = httpx.post(upload_url, headers=headers, content=image_bytes, timeout=15)
    response.raise_for_status()

    return (
        f"{settings.SUPABASE_URL}/storage/v1/object/public/"
        f"{settings.SUPABASE_BUCKET}/{filename}"
    )
