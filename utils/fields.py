from rest_framework import serializers
from .constants import grade_labels
import uuid, base64, boto3, environ
from boto3.s3.transfer import TransferConfig
from django.core.files.uploadedfile import UploadedFile
from botocore.exceptions import NoCredentialsError
from mypy_boto3_s3 import S3Client
from io import BytesIO
from typing import Optional
env = environ.Env()
environ.Env.read_env()
s3: S3Client = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'), region_name='us-west-1')

MAX_SIZE_MB = 1
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024 

BUCKET = 'climberseye'

class UrlField(serializers.Field):
    """
    Take post request's image data and process it to a usable s3 image url which will be stored in database.
    Any response where image is needed will only be sent the processed image url.
    """

    def to_internal_value(self, data: UploadedFile):
        return self.process_image(data)
    
    def to_representation(self, value):
        # Just return the value as it is stored in the model
        return value
    
    def process_image(self, image: UploadedFile):
        """
        Storing the uploaded file image in S3 bucket, and the URL will be returned.
        """
        if not image:
            return None
        try:
            folder = self.get_prefix_folder()
            s3_key = f"{folder}/{image.name}-{str(uuid.uuid4())}.jpg"
            s3.upload_fileobj(Fileobj=image, Bucket=BUCKET, Key=s3_key, ExtraArgs={'ContentType': image.content_type})
            image_url = f"https://{BUCKET}.s3.amazonaws.com/{s3_key}"
            return image_url
        except NoCredentialsError:
            raise serializers.ValidationError("AWS credentials are missing or incorrect.")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred while uploading the image: {str(e)}")
    
    def get_prefix_folder(self):
        match self.label:
            case 'spraywall_image':
                return 'spraywall'
            case 'boulder_image':
                return 'boulder'
            case 'profile_image':
                return 'profile'
            case _:
                pass
    
class GradeField(serializers.Field):
    def to_internal_value(self, grade: str):
        return grade_labels.index(grade)
    def to_representation(self, grade: int):
        return grade_labels[grade]