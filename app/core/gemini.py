import json
import time

from google import genai
from google.genai import types

from app.core.config import settings
from app.core import groq_fallback

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1


# field_key values match app/core/compliance.py's rule keys one-to-one.
# Always-return-all-5 (with value="" for anything not visible) matters:
# the compliance engine matches on field_key, not on label text, so a
# missing key would silently skip that rule's check instead of failing it.
EXTRACTION_PROMPT = """You are reading a packaged-commodity label photo for a
Legal Metrology compliance check in India. Extract these 5 fields:

- field_key "manufacturer": manufacturer/packer/importer name & address
- field_key "net_quantity": net quantity, including its unit
- field_key "mfg_date": month and year of manufacture
- field_key "mrp": maximum retail price
- field_key "consumer_care": consumer care name/address/phone/email

Always return all 5 field_keys, even if a field isn't visible on the
label — in that case set "value" to "" and "confidence" to "low".
Never omit a field_key from the array.

Return a JSON array in this exact shape:
[{"id": "0", "field_key": "manufacturer", "label": "Manufacturer Details",
  "value": "...", "confidence": "high" or "low"}]
"""


def _generate_with_retry(*args, **kwargs):
    """
    Make a Gemini request and retry transient failures such as 503.
    Uses exponential backoff: 1s -> 2s -> 4s.
    """

    for attempt in range(MAX_RETRIES):
        try:
            return _client.models.generate_content(*args, **kwargs)

        except Exception as exc:
            # Don't retry forever.
            if attempt == MAX_RETRIES - 1:
                raise

            delay = INITIAL_RETRY_DELAY * (2**attempt)

            print(
                f"Gemini request failed "
                f"(attempt {attempt + 1}/{MAX_RETRIES}): {exc}. "
                f"Retrying in {delay}s..."
            )

            time.sleep(delay)


def extract_fields_from_image(
    image_bytes: bytes,
    mime_type: str,
) -> list[dict]:
    try:
        response = _generate_with_retry(
            model=settings.GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)

    except Exception as gemini_exc:
        # Gemini's free tier gets rate-limited hard under real-world
        # traffic (it's a popular free model for exactly this kind of
        # project). Fall back to Groq's free vision model rather than
        # fail the whole scan outright — only if a key is configured.
        if not groq_fallback.is_configured():
            raise

        print(f"Gemini exhausted retries ({gemini_exc}). Falling back to Groq.")
        try:
            return groq_fallback.extract_fields_from_image(image_bytes, mime_type)
        except Exception as groq_exc:
            # Without this, the real Groq failure reason is invisible —
            # it was propagating straight to scans.py's generic 502.
            print(f"Groq fallback also failed: {groq_exc}")
            raise


# check_compliance() has moved to app/core/compliance.py — it's now a
# deterministic Python rule engine, not a second Gemini call. See that
# file for the rationale (latency, reproducibility, auditability).
