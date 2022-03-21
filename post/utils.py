from PIL import Image
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile


def image_process(file):
    """
    :param request:
        image file
    :return:
        File/None
    """
    try:
        img = Image.open(file)
        image_format = ['JPEG', 'PNG', 'TIFF', 'EPS', 'RAW']
        if img.format in image_format:
            img.convert('RGB')

            img.thumbnail((640, 480), Image.ANTIALIAS)
            thumbnailString = BytesIO()
            if file.size > 5242880:
                if img.mode in ("RGBA", "P"):
                    img.save(thumbnailString, 'PNG', quality=50)
                else:
                    img.save(thumbnailString, 'JPEG', quality=50)
            else:
                if img.mode in ("RGBA", "P"):
                    img.save(thumbnailString, 'PNG', quality=100)
                else:
                    img.save(thumbnailString, 'JPEG', quality=100)
            newFile = InMemoryUploadedFile(thumbnailString, None, 'temp.jpg', 'image/jpeg', thumbnailString, None)
            return newFile
        else:
            return None
    except Exception as e:
        return None

