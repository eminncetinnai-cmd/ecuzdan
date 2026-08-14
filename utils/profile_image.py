"""Profile image download and storage utility.

This module handles downloading profile pictures from OAuth providers
and saving them to the local filesystem.
"""

import logging
import os
import secrets
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'profiles')
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def ensure_upload_folder():
    """Ensure the upload folder exists."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def download_profile_image(image_url: str) -> str | None:
    """Download profile image from URL and save to local filesystem.

    Args:
        image_url: URL of the profile image

    Returns:
        Local path to the saved image, or None if download fails
    """
    if not image_url:
        return None

    try:
        # Download image
        response = requests.get(image_url, timeout=10, stream=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"Invalid content type for profile image: {content_type}")
            return None

        # Check file size
        content_length = int(response.headers.get('content-length', 0))
        if content_length > MAX_IMAGE_SIZE:
            logger.warning(f"Profile image too large: {content_length} bytes")
            return None

        # Generate unique filename
        ext = get_extension_from_url(image_url) or '.jpg'
        filename = f"{secrets.token_hex(16)}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Save image
        ensure_upload_folder()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Profile image saved: {filepath}")
        return f"/static/uploads/profiles/{filename}"

    except Exception as e:
        logger.error(f"Failed to download profile image: {e}")
        return None


def get_extension_from_url(url: str) -> str | None:
    """Extract file extension from URL.

    Args:
        url: URL to extract extension from

    Returns:
        File extension including dot (e.g., '.jpg'), or None
    """
    parsed = urlparse(url)
    path = parsed.path
    for ext in ALLOWED_EXTENSIONS:
        if path.lower().endswith(ext):
            return ext
    return None


def delete_profile_image(image_path: str) -> bool:
    """Delete profile image from filesystem.

    Args:
        image_path: Path to the image file

    Returns:
        True if deletion successful, False otherwise
    """
    if not image_path:
        return False

    try:
        # Convert URL path to filesystem path
        if image_path.startswith('/'):
            image_path = image_path.lstrip('/')
        filepath = os.path.join(os.getcwd(), image_path)

        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Profile image deleted: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete profile image: {e}")
        return False
