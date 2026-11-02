"""Validation helpers for property listings and uploaded images."""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def validate_image(data: bytes, filename: str = "image") -> tuple[bool, str | None]:
    """Check size, actual image contents, and supported format (not extension alone)."""
    if not data:
        return False, f"{filename} is empty."
    if len(data) > MAX_IMAGE_BYTES:
        return False, f"{filename} is larger than 15 MB."
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in SUPPORTED_FORMATS:
                return False, f"{filename} must be JPG, PNG, or WEBP."
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError):
        return False, f"{filename} is not a valid image. Please choose a JPG, PNG, or WEBP file."
    return True, None


def validate_property(name: str, location: str, image_count: int) -> list[str]:
    errors = []
    if not name.strip():
        errors.append("Enter a property name.")
    if not location.strip():
        errors.append("Enter a property location.")
    if not 4 <= image_count <= 8:
        errors.append("Upload between 4 and 8 property photos.")
    return errors
