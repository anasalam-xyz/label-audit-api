"""Small, stateless image preprocessing helpers for label extraction."""

import cv2
import numpy as np


_MAX_IMAGE_SIDE = 1600
_JPEG_QUALITY = 85


def _deskew(image: np.ndarray) -> np.ndarray:
    """Rotate an image when its edges provide a sufficiently clear angle."""

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(
        edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
    )

    height, width = gray.shape
    image_area = float(height * width)
    candidates: list[tuple[float, float]] = []

    for contour in contours:
        if cv2.contourArea(contour) < image_area * 0.001:
            continue

        rect = cv2.minAreaRect(contour)
        rect_width, rect_height = rect[1]
        rect_area = rect_width * rect_height
        if rect_area <= 0 or rect_area < image_area * 0.002:
            continue

        angle = float(rect[2])
        if angle < -45:
            angle += 90

        # Very small estimates are noise, while large ones are usually a
        # bad contour (for example, a picture boundary or an object edge).
        if 0.5 <= abs(angle) <= 30:
            candidates.append((rect_area, angle))

    if not candidates:
        return image

    # Prefer the largest clear contour, which is generally the label/text
    # block, and reject a result when there is no meaningful consensus.
    candidates.sort(reverse=True)
    angle = candidates[0][1]
    if len(candidates) > 1:
        comparable = [item[1] for item in candidates if item[0] >= candidates[0][0] * 0.5]
        if np.median(comparable) * angle <= 0:
            return image
        angle = float(np.median(comparable))

    if abs(angle) > 30:
        return image

    center = (width / 2.0, height / 2.0)
    rotation = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image,
        rotation,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE to luminance while retaining the image's color."""

    try:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        lightness, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lightness = clahe.apply(lightness)
        return cv2.cvtColor(
            cv2.merge((lightness, a_channel, b_channel)), cv2.COLOR_LAB2BGR
        )
    except cv2.error:
        return image


def preprocess_image(image_bytes: bytes) -> bytes:
    """Preprocess image bytes and return a compact JPEG suitable for Gemini."""

    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image: corrupt or unsupported image data")

    try:
        image = _deskew(image)
    except cv2.error:
        # Deskew is an optional improvement; retain the decoded image if it
        # cannot be computed for an unusual image.
        pass

    image = _enhance_contrast(image)

    height, width = image.shape[:2]
    longest_side = max(height, width)
    if longest_side > _MAX_IMAGE_SIDE:
        scale = _MAX_IMAGE_SIDE / longest_side
        image = cv2.resize(
            image,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )

    success, output = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
    )
    if not success:
        raise ValueError("Unable to encode preprocessed image as JPEG")
    return output.tobytes()
