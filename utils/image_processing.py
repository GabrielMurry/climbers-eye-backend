from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps, ImageEnhance
import base64
import numpy as np
from cv2 import imencode

class ImageProcessor:
    @staticmethod
    def prep_files(photo_file: UploadedFile, canvas_file: UploadedFile) -> tuple[Image.Image, Image.Image]:
        image = Image.open(photo_file).convert("RGBA")
        canvas = Image.open(canvas_file)
        photo_image = ImageOps.exif_transpose(image)
        drawing_image = ImageOps.exif_transpose(canvas).resize(photo_image.size)
        return photo_image, drawing_image

    @staticmethod
    def increase_drawing_opacity(drawing_image: Image.Image) -> Image.Image:
        r, g, b, a = drawing_image.split()
        a = a.point(lambda x: x * 2)
        return Image.merge('RGBA', (r, g, b, a))

    @staticmethod
    def mask_drawing(drawing_image: Image.Image, photo_image: Image.Image) -> Image.Image:
        mask = Image.new("L", drawing_image.size, 'WHITE')
        mask.paste(drawing_image, mask=drawing_image)
        return Image.composite(drawing_image, photo_image, mask)

    @staticmethod
    def combine_images(drawing_image: Image.Image, photo_image: Image.Image) -> Image.Image:
        alpha_channel = photo_image.getchannel('A')
        gray_channels = photo_image.convert('L')
        photo_image_result = Image.merge('RGBA', (gray_channels, gray_channels, gray_channels, alpha_channel))
        photo_image_result = ImageEnhance.Brightness(photo_image_result).enhance(0.4)
        photo_image_result.alpha_composite(drawing_image)
        return photo_image_result

    @staticmethod
    def convert_image_to_base64(image: Image.Image) -> str:
        image_arr = np.array(image)
        _, byte_data = imencode('.png', image_arr)
        return base64.b64encode(byte_data).decode("utf-8")