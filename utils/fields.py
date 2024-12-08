from rest_framework import serializers
from .constants import grade_labels
import uuid, base64, boto3, environ
from boto3.s3.transfer import TransferConfig
from io import BytesIO
from PIL import Image
from botocore.exceptions import NoCredentialsError
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

MAX_SIZE_MB = 1
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024  # 4MB in bytes

class UrlField(serializers.Field):
    """
    Take post request's base64 image data and process it to a usable s3 image url which will be stored in database.
    Any response where image is needed will only be sent the processed image url.
    """
    def to_internal_value(self, data):
        return self.process_image(data)
    
    def to_representation(self, value):
        # Just return the value as it is stored in the model
        return value
    
    def process_image(self, image):
        """
        Convert a multi-part form data image to an S3 image URL.
        The image will be stored in an S3 bucket, and the URL will be returned.
        """
        if not image:
            return None
        try:
            print('1')
            # Generate a unique key or filename for the image in S3
            s3_key = f"images/{str(uuid.uuid4())}.jpg"
            print('2')
            # Ensure the image is a file-like object (if necessary)
            if not hasattr(image, 'read'):
                # Decode the base64 image data
                image_data = base64.b64decode(image)
                # Create a file-like object from the decoded image data
                image = BytesIO(image_data)
            print('3')
            # Upload the image data to S3 bucket
            s3.upload_fileobj(image, 'sprayimages', s3_key)
            print('4')
            # Construct the S3 URL for the uploaded image
            image_url = f"https://sprayimages.s3.amazonaws.com/{s3_key}"
            print('5')
            return image_url
        except NoCredentialsError:
            raise serializers.ValidationError("AWS credentials are missing or incorrect.")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred while uploading the image: {str(e)}")
    
class GradeField(serializers.Field):
    def to_internal_value(self, grade: str):
        return grade_labels.index(grade)
    def to_representation(self, grade: int):
        return grade_labels[grade]