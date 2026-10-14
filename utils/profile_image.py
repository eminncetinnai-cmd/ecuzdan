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


def optimize_image_file(source, target_path: str, max_dim: int = 400, quality: int = 85) -> bool:
    """Resize and optimize an image file for profile display.

    Converts image to maximum bounding box of max_dim x max_dim and compresses
    it to reduce storage footprint and load times. Handles EXIF orientation.
    Gracefully falls back to raw copy if Pillow processing is unavailable or fails.

    Args:
        source: File path (str) or file-like object (e.g. Werkzeug FileStorage / BytesIO)
        target_path: Destination file path
        max_dim: Maximum width/height in pixels (default 400)
        quality: JPEG/WebP compression quality (default 85)

    Returns:
        bool: True if processed successfully, False otherwise
    """
    try:
        from PIL import Image, ImageOps

        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

        with Image.open(source) as img:
            img = ImageOps.exif_transpose(img) or img

            target_ext = os.path.splitext(target_path)[1].lower()
            save_kwargs = {'optimize': True}

            if target_ext in ('.jpg', '.jpeg'):
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                save_kwargs['quality'] = quality
            elif target_ext == '.webp':
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
                save_kwargs['quality'] = quality
            elif target_ext == '.png':
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')

            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            img.save(target_path, **save_kwargs)
            return True
    except Exception as e:
        logger.debug("Profile image optimization fallback: %s", e)
        if isinstance(source, str) and os.path.exists(source) and source != target_path:
            import shutil
            shutil.copy2(source, target_path)
            return True
        elif hasattr(source, 'save') and callable(source.save):
            source.seek(0)
            source.save(target_path)
            return True
        return False


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

        # Optimize image to standard avatar dimension in place if valid image
        try:
            optimize_image_file(filepath, filepath)
        except Exception:
            pass

        logger.info(f"Profile image saved: {filepath}")
        return f"/static/uploads/profiles/{filename}"

    except Exception as e:
        # OAuth sağlayıcısındaki geçici/kayıp görseller fallback ile tolere edilir.
        logger.warning("Failed to download profile image (expected for missing OAuth assets): %s", e)
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
