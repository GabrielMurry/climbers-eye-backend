from rest_framework import status, generics, permissions
from .serializers import SprayWallSerializer
from .models import SprayWall
from urllib.parse import urlparse
from rest_framework.response import Response
import boto3, environ
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

class SpraywallList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SprayWallSerializer

    def get_queryset(self):
        gym_id = self.kwargs['gym_id']
        return SprayWall.objects.filter(gym=gym_id)
    
class SpraywallDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = SprayWall.objects.all()
    serializer_class = SprayWallSerializer

    def delete(self, request, *args, **kwargs):
        spraywall_instance = self.get_object()
        try:
            self.delete_image_from_s3(spraywall_instance.image_url)
        except Exception as e:
            return Response({"error": f"Failed to delete image from S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # If the S3 deletion was successful, proceed to delete the SprayWall instance
        return super().destroy(request, *args, **kwargs)
    
    def delete_image_from_s3(self, image_url):
        parsed_url = urlparse(image_url)
        bucket_name = 'sprayimages'
        s3_key = parsed_url.path.lstrip('/')
        # Delete the object from the S3 bucket
        s3.delete_object(Bucket=bucket_name, Key=s3_key)