import base64
import json

from groq import Groq

from app.core.config import settings

_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

# Same field contract as gemini.py's EXTRACTION_PROMPT — field_key values
# must match exactly, or compliance.py's rule matching silently breaks.
# Wrapped in a top-level object (not a bare array) because Groq's JSON
# mode requires an object, unlike Gemini's response_mime_type=json setting.
GROQ_EXTRACTION_PROMPT = """You are reading a packaged-commodity label photo for a
Legal Metrology compliance check in India. Extract these 5 fields:

- field_key "manufacturer": manufacturer/packer/importer name & address
- field_key "net_quantity": net quantity, including its unit
- field_key "mfg_date": month and year of manufacture
- field_key "mrp": maximum retail price
- field_key "consumer_care": consumer care name/address/phone/email

Always return all 5 field_keys, even if a field isn't visible on the
label — in that case set "value" to "" and "confidence" to "low".
Never omit a field_key.

Return a JSON object in this exact shape:
{"fields": [{"id": "0", "field_key": "manufacturer", "label": "Manufacturer Details",
  "value": "...", "confidence": "high" or "low"}]}
"""


def is_configured() -> bool:
    return _client is not None


def extract_fields_from_image(image_bytes: bytes, mime_type: str) -> list[dict]:
    """
    Fallback extraction path, used only when Gemini is exhausted (see
    gemini.py). Not called if GROQ_API_KEY isn't set — extract_fields_
    from_image() in gemini.py checks is_configured() first and lets the
    original Gemini error propagate if there's no fallback available.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    completion = _client.chat.completions.create(
        model=settings.GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": GROQ_EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                    },
                ],
            }
        ],
        temperature=0,
        max_completion_tokens=1024,
        response_format={"type": "json_object"},
    )

    parsed = json.loads(completion.choices[0].message.content)
    return parsed["fields"]
