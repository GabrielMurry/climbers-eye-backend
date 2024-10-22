from PIL import Image, ImageFilter
import base64
from io import BytesIO
import requests

def create_blurred_placeholder(image_url=None, base64_string=None):
    if base64_string:
        # Convert base64 to image
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
    elif image_url:
        # Fetch the image from S3 URL
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
    
    original_size = image.size  # Store original dimensions

    # Resize to low resolution and blur
    image = image.resize((20, 20))  # Resize to a small resolution for the "low-res" effect
    image = image.filter(ImageFilter.GaussianBlur(5))  # Apply Gaussian Blur
    
    # Resize back to original dimensions to maintain aspect ratio
    image = image.resize(original_size, Image.LANCZOS)
     # Reduce the number of colors (indexed image)
    image = image.convert("P", palette=Image.ADAPTIVE, colors=32)  # Reduce to 32 colors

    # Convert back to base64p
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=5)
    blurred_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return blurred_base64