"""
Deterministic Legal Metrology compliance rule engine.

Replaces the previous Gemini-based check_compliance() call. Rules are
plain Python matched against structured extracted fields — no LLM call,
no added latency, fully reproducible: the same input always produces the
same verdict, and every violation traces back to a rule id and the
observed value that failed it, not a model's judgment call.

Mirrors: frontend/lib/rule-aspects.ts — keep the field_key/rule_code set
in sync between the two by hand until there's a shared source of truth.
"""

import re

# Field keys the extraction step always returns — one per rule below.
# See EXTRACTION_PROMPT in core/gemini.py; it's instructed to return all
# 5 keys every time, with value="" for anything not visible on the label.
MANUFACTURER = "manufacturer"
NET_QUANTITY = "net_quantity"
MFG_DATE = "mfg_date"
MRP = "mrp"
CONSUMER_CARE = "consumer_care"

# Recognized net-quantity units under the standard-units requirement.
_UNIT_PATTERN = re.compile(
    r"\d+(\.\d+)?\s*(g|kg|mg|ml|l|gm|gms|litre|litres|liter|liters)\b",
    re.IGNORECASE,
)

# MM/YYYY, "Month YYYY", or DD/MM/YYYY style manufacture dates.
_DATE_PATTERN = re.compile(
    r"(\d{1,2}[/\-]\d{4})|"
    r"([A-Za-z]{3,9}\s+\d{4})|"
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})"
)

# A rupee amount: ₹/Rs. prefix, or a bare number with up to 2 decimals.
_MRP_PATTERN = re.compile(r"(₹|rs\.?)\s*\d+|\d+(\.\d{1,2})?", re.IGNORECASE)

# A 10-digit phone number or an email address.
_CONTACT_PATTERN = re.compile(r"(\d{10})|([\w.+-]+@[\w-]+\.[a-zA-Z]{2,})")


def _get(fields_by_key: dict, key: str) -> str:
    field = fields_by_key.get(key)
    return (field.get("value") or "").strip() if field else ""


def check_compliance(fields: list[dict]) -> list[dict]:
    """
    Check extracted label fields against the 5 implemented LMPC rules.

    Input: fields with a stable `field_key` (see core/gemini.py's
    EXTRACTION_PROMPT). Output: violations in the same shape the old
    Gemini-based check returned — [{"rule_code": ..., "explanation": ...}]
    — so schemas/scan.py and the frontend don't need to change.
    """
    fields_by_key = {f.get("field_key"): f for f in fields if f.get("field_key")}
    violations = []

    manufacturer = _get(fields_by_key, MANUFACTURER)
    if not manufacturer:
        violations.append({
            "rule_code": "Rule 6(1)(c)",
            "explanation": "Manufacturer name and address are not visible on the label.",
        })

    net_quantity = _get(fields_by_key, NET_QUANTITY)
    if not net_quantity:
        violations.append({
            "rule_code": "Rule 6(1)(d)",
            "explanation": "Net quantity is not declared on the label.",
        })
    elif not _UNIT_PATTERN.search(net_quantity):
        violations.append({
            "rule_code": "Rule 6(1)(d)",
            "explanation": f"Net quantity '{net_quantity}' isn't in a standard unit (g/kg/ml/l).",
        })

    mfg_date = _get(fields_by_key, MFG_DATE)
    if not mfg_date:
        violations.append({
            "rule_code": "Rule 6(1)(e)",
            "explanation": "Month and year of manufacture are not visible on the label.",
        })
    elif not _DATE_PATTERN.search(mfg_date):
        violations.append({
            "rule_code": "Rule 6(1)(e)",
            "explanation": f"Manufacture date '{mfg_date}' isn't in a recognizable date format.",
        })

    mrp = _get(fields_by_key, MRP)
    if not mrp:
        violations.append({
            "rule_code": "Rule 6(1)(f)",
            "explanation": "MRP is not declared on the label.",
        })
    elif not _MRP_PATTERN.search(mrp):
        violations.append({
            "rule_code": "Rule 6(1)(f)",
            "explanation": f"MRP '{mrp}' doesn't look like a valid price.",
        })
    # NOTE: the minimum-4mm-font requirement (Rule 6(1)(f)) can't be
    # checked here — verifying printed font height needs bounding-box
    # geometry plus a physical scale reference, which this pipeline
    # doesn't capture. The previous Gemini-based check couldn't verify
    # this either: it only ever received extracted text, never the
    # image, so it was never actually measuring font size.

    consumer_care = _get(fields_by_key, CONSUMER_CARE)
    if not consumer_care:
        violations.append({
            "rule_code": "Rule 6(1)(h)",
            "explanation": "Consumer care details are not visible on the label.",
        })
    elif not _CONTACT_PATTERN.search(consumer_care):
        violations.append({
            "rule_code": "Rule 6(1)(h)",
            "explanation": f"Consumer care info '{consumer_care}' has no recognizable phone number or email.",
        })

    return violations
