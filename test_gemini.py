"""
Standalone Gemini SDK smoke test — run this BEFORE trusting app/core/gemini.py
inside a live route. Tests the raw SDK call shape first (so any SDK version
mismatch shows up as a clear error), then your actual wrapper functions.

Usage:
    uv run python test_gemini.py path/to/label_photo.jpg

Place this file at your project root (same level as app/, pyproject.toml).
"""

import sys
import json
from pathlib import Path

# --- Step 0: confirm the key is actually loading ---------------------------
try:
    from app.core.config import settings
except ImportError as e:
    print("Could not import app.core.config — run this from the project root")
    print(f"Error: {e}")
    sys.exit(1)

if not settings.GEMINI_API_KEY:
    print("GEMINI_API_KEY is empty — check your .env file is being picked up")
    sys.exit(1)

masked = settings.GEMINI_API_KEY[:4] + "…" + settings.GEMINI_API_KEY[-4:]
print(f"[ok] GEMINI_API_KEY loaded ({masked})")
print(f"[ok] Using model: {settings.GEMINI_MODEL}")

# --- Step 1: get the test image ---------------------------------------------
if len(sys.argv) < 2:
    print("\nUsage: uv run python test_gemini.py path/to/label_photo.jpg")
    sys.exit(1)

image_path = Path(sys.argv[1])
if not image_path.exists():
    print(f"File not found: {image_path}")
    sys.exit(1)

image_bytes = image_path.read_bytes()
mime_type = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
print(f"[ok] Loaded {image_path.name} ({len(image_bytes)} bytes, {mime_type})")

# --- Step 2: raw SDK call, bypassing your wrapper ---------------------------
# This isolates whether a failure is the SDK shape itself, vs. something in
# your app/core/gemini.py wrapper logic.
print("\n--- Testing raw SDK call shape ---")
try:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            "Describe this image in one sentence.",
        ],
    )
    print(f"[ok] Raw SDK call succeeded")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"[FAIL] Raw SDK call failed: {type(e).__name__}: {e}")
    print("\nThis means the SDK method signatures in app/core/gemini.py are")
    print("likely wrong for your installed google-genai version. Check:")
    print("  uv run python -c \"import google.genai; print(google.genai.__file__)\"")
    print("and inspect the installed package's own examples/docstrings.")
    sys.exit(1)

# --- Step 3: your actual wrapper functions -----------------------------------
print("\n--- Testing app/core/gemini.py wrapper: extract_fields_from_image ---")
try:
    from app.core.gemini import extract_fields_from_image, check_compliance

    fields = extract_fields_from_image(image_bytes, mime_type)
    print(f"[ok] extract_fields_from_image returned {len(fields)} fields:")
    print(json.dumps(fields, indent=2))
except Exception as e:
    print(f"[FAIL] extract_fields_from_image failed: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n--- Testing app/core/gemini.py wrapper: check_compliance ---")
try:
    violations = check_compliance(fields)
    print(f"[ok] check_compliance returned {len(violations)} violations:")
    print(json.dumps(violations, indent=2))
except Exception as e:
    print(f"[FAIL] check_compliance failed: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n[ok] All checks passed — safe to wire into the live routes.")
