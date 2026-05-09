"""File storage operations: atomic writes, directory management"""

import os
import shutil
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def is_image_file(path: str) -> bool:
    """Check if file is a supported image format"""
    return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS


def atomic_write(target_path: str, content: str, encoding: str = "utf-8"):
    """Write file atomically: write to temp file then rename.
    
    This prevents partial writes on crash.
    """
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=target_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        # On Windows, need to remove target first if exists
        if os.path.exists(target_path):
            os.replace(tmp_path, target_path)
        else:
            os.rename(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def ensure_dir(path: str) -> str:
    """Ensure directory exists, return the path"""
    os.makedirs(path, exist_ok=True)
    return path


def find_paired_label(image_path: str, label_dir: str) -> Optional[str]:
    """Find the YOLO txt label file paired with an image.
    
    YOLO convention: images/0001.jpg -> labels/0001.txt
    """
    basename = os.path.splitext(os.path.basename(image_path))[0]
    label_path = os.path.join(label_dir, basename + ".txt")
    if os.path.exists(label_path):
        return label_path
    return None


def scan_image_dir(image_dir: str) -> list:
    """Scan directory for image files, return sorted list of paths"""
    if not os.path.isdir(image_dir):
        return []
    images = []
    for f in sorted(os.listdir(image_dir)):
        full_path = os.path.join(image_dir, f)
        if os.path.isfile(full_path) and is_image_file(full_path):
            images.append(full_path)
    return images


def get_image_size(image_path: str) -> Optional[tuple]:
    """Get image width and height without loading full image"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception:
        return None


def copy_file(src: str, dst: str):
    """Copy file, creating destination directory if needed"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
