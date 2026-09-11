import json
import time

from google import genai
from google.genai import types

from app.core.config import settings

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1


EXTRACTION_PROMPT = """You are reading a packaged-commodity label photo for a
Legal Metrology compliance check in India. Extract these fields if visible:
manufacturer name & address, net quantity, MRP, month/year of manufacture,
consumer care details.

Return a JSON array in this exact shape:
[{"id": "0", "label": "...", "value": "...", "confidence": "high" or "low"}]
"""


RULES_TEXT = """
Legal Metrology (Packaged Commodities) Rules, 2011 — key checks:
- Rule 6(1)(c): manufacturer name and complete address must be present.
- Rule 6(1)(d): net quantity must be declared in standard units.
- Rule 6(1)(e): month and year of manufacture must be present.
- Rule 6(1)(f): MRP must be declared inclusive of all taxes, min. 4mm font.
- Rule 6(1)(h): consumer care name/address/phone/email must be present.
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


def check_compliance(fields: list[dict]) -> list[dict]:
    prompt = (
        "You are a Legal Metrology compliance checker. "
        f"Given these rules:\n\n"
        f"{RULES_TEXT}\n\n"
        "Check these extracted label fields and list violations as a JSON array:\n"
        '[{"rule_code": "Rule 6(1)(f)", "explanation": "plain language"}]\n'
        "Return [] if fully compliant.\n\n"
        f"Fields: {json.dumps(fields)}"
    )

    response = _generate_with_retry(
        model=settings.GEMINI_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)
