import uuid

from django.core.files import File
from pathlib import Path
from PIL import Image
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models

image_types = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "gif": "GIF",
    "tif": "TIFF",
    "tiff": "TIFF",
}



