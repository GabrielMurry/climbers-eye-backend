from rest_framework import status, generics, permissions
from .serializers import SprayWallSerializer
from .models import SprayWall
from urllib.parse import urlparse
from rest_framework.response import Response
from rest_framework.request import Request
from utils.thumbnail import generate_thumbnail
from mypy_boto3_s3 import S3Client
import boto3, environ
env = environ.Env()
environ.Env.read_env()
s3: S3Client = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))
from utils.image import TestImage
from django.core.files.uploadedfile import UploadedFile

class SpraywallList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SprayWallSerializer

    def get_queryset(self):
        gym_id = self.kwargs['gym_id']
        return SprayWall.objects.filter(gym=gym_id)
    
    def post(self, request: Request, *args, **kwargs):
        # Data payload is a multi part form data rather than json
        # Reconfigure data into json form
        data = {}
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            print("No file uploaded or file not found in request.FILES.")
        # print(f"File received: {uploaded_file.name}, Size: {uploaded_file.size}, Content-Type: {uploaded_file.content}")
        if not isinstance(uploaded_file, UploadedFile):
            print("Invalid file object type.")
        width = request.data.get('width')
        height = request.data.get('height')
        name = request.data.get('name')
        gym = request.data.get('gym')
        data['url'] = uploaded_file
        data['name'] = name
        data['width'] = width
        data['height'] = height
        data['gym'] = gym
        thumbnail_uploaded_file = generate_thumbnail(uploaded_file, name)
        data['thumbnailUrl'] = thumbnail_uploaded_file
        # # _full_data is the private attribute holding request.data
        request._full_data = data
        return super().post(request, *args, **kwargs)
    
class SpraywallDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = SprayWall.objects.all()
    serializer_class = SprayWallSerializer
    
    def patch(self, request, *args, **kwargs):
        spraywall_instance = self.get_object()
        # If user is updating spraywall image, replace existing image.
        # Spraywall image is required so it already exists. Therefore, if patching image, delete the original from s3 buckets.
        if request.data['url']:
            self.delete_image_from_s3(spraywall_instance.image_url)
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        spraywall_row = SprayWall.objects.get(id=kwargs['pk'])
        self.delete_image_from_s3(spraywall_row.image_url)
        # If the S3 deletion was successful, proceed to delete the SprayWall instance
        return super().destroy(request, *args, **kwargs)
    
    def delete_image_from_s3(self, image_url: str):
        try:
            parsed_url = urlparse(image_url)
            s3_key = parsed_url.path.lstrip('/')
            # Delete the object from the S3 bucket
            s3.delete_object(Bucket=env('BUCKET'), Key=s3_key)
        except Exception as e:
            return Response({"error": f"Failed to delete image from S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)