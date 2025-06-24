from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile

def generate_thumbnail(image: UploadedFile | None, name: str) -> InMemoryUploadedFile | None:
    if image is None: 
        return None
    # Make a copy of the uploaded file alt wall. Performing image manipulation with PIL will usually mutate the variable.
    image_copy = BytesIO(image.read())
    image.seek(0)
    thumbnail = _resize_image_to_720p(image_copy)
    # Convert thumbnail image (which is a PIL image) to an InMemoryUploadedFile type.
    in_mem_file = BytesIO()
    thumbnail.save(in_mem_file, format="JPEG")
    in_mem_file.seek(0)
    return InMemoryUploadedFile(
        file=in_mem_file,
        field_name=None,
        name=name,
        content_type=f'image/jpg',
        size=in_mem_file.getbuffer().nbytes,
        charset=None
    )

def _resize_image_to_720p(image: UploadedFile) -> Image:
    """
    Resizes an UploadedFile image to 720p (1280x720) using PIL.

    Args:
        image (UploadedFile): Image of UploadedFile type.
    """
    try:
        img = Image.open(image)
        img = ImageOps.exif_transpose(img)
        width, height = img.size

        # Calculate the new dimensions while maintaining aspect ratio
        if width / height > 1280 / 720:
            new_width = 1280
            new_height = int(height * (1280 / width))
        else:
            new_height = 720
            new_width = int(width * (720 / height))

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        resized_img.save("resized_image.jpg", format="png", optimize=True, quality=85)
        return resized_img
    except FileNotFoundError:
        print(f"Error: Image file not found at {image}")
    except Exception as e:
        print(f"An error occurred: {e}")