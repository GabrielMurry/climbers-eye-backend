from rest_framework import serializers
from climbers_eye_backend.utils.constants import grade_labels
from climbers_eye_backend.models import Boulder, Send
import uuid, base64, boto3, environ
from io import BytesIO
from botocore.exceptions import NoCredentialsError
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

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
    
    def process_image(self, base64_image):
        """
        Convert image data (which is a large base64 image data) to s3 image url.
        The image will be stored in s3 bucket, and the url will be returned.
        """
        try:
            # Decode the base64 image data
            image_data = base64.b64decode(base64_image)
            # Create a file-like object from the decoded image data
            image_file = BytesIO(image_data)
            # Generate a unique key or filename for the image in S3
            s3_key = f"images/{str(uuid.uuid4())}.jpg"
            # Upload the image data to your S3 bucket
            s3.upload_fileobj(image_file, 'sprayimages', s3_key)
            # Construct the S3 URL for the uploaded image
            image_url = f"https://sprayimages.s3.amazonaws.com/{s3_key}"
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