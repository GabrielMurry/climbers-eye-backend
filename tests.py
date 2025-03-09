from django.test import TestCase
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
import boto3, environ, uuid
env = environ.Env()
environ.Env.read_env()
from botocore.config import Config
from mypy_boto3_s3 import S3Client
from utils.image_processing import ImageProcessor

BUCKET = 'climberseye'
PREFIX_FOLDER = 'boulder'

class ImageUploadTest(TestCase):
    # def test_image_upload(self):
    #     s3: S3Client = boto3.client(
    #         's3', 
    #         aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
    #         aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY')
    #     )
    #     s3_key = f"{PREFIX_FOLDER}/cat-{str(uuid.uuid4())}.jpg"
    #     s3.upload_file(Filename='images/cat.jpg', Bucket=BUCKET, Key=s3_key)   

    def test_image_composite(self):
        photo_image, drawing_image = ImageProcessor.prep_files('images/photo.jpg', 'images/canvas.jpg')
        drawing_image = ImageProcessor.increase_drawing_opacity(drawing_image)
        drawing_image = ImageProcessor.mask_drawing(drawing_image, photo_image)
        drawing_image.show()
        # result_image = ImageProcessor.combine_images(drawing_image, photo_image)