from rest_framework import generics, permissions
from django.db import transaction
from .serializers import GymSerializer
from ..auth.serializers import PersonSerializer
from .models import Gym
from ..spraywall.models import SprayWall
from ..boulder.models import Boulder
from urllib.parse import urlparse
import boto3
import environ
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

class GymList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GymSerializer
    # filter_backends = (filters.DjangoFilterBackend,)
    # filterset_class = GymFilter
    # pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Gym.objects.all()
    
# put this in user views?    
class UserChooseGym(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PersonSerializer

    def get_object(self):
        # Return the currently authenticated user
        return self.request.user
    
class GymDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Gym.objects.all()
    serializer_class = GymSerializer

    def delete(self, request, *args, **kwargs):
        """
        If a gym is deleted, its spraywalls are deleted. 
        A spraywall can have many boulders. Delete boulder images from s3, then delete the spraywall image from s3.
        Do this to every spraywall in the gym, then delete the gym
        """
        # Using transaction.atomic() ensures that the database operations are atomic, meaning if anything fails, none of the deletions are committed. 
        # This ensures consistency.
        with transaction.atomic():
            spraywall_queryset = SprayWall.objects.filter(gym=kwargs['pk'])
            for spraywall in spraywall_queryset:
                boulder_queryset = Boulder.objects.filter(spraywall=spraywall.id)
                for boulder in boulder_queryset:
                    self.delete_image_from_s3(boulder.image_url)
                self.delete_image_from_s3(spraywall.image_url)
            # Cascade deletion will handle removing the spraywalls and boulders from the database
            return super().destroy(request, *args, **kwargs)
    
    def delete_image_from_s3(self, image_url):
        parsed_url = urlparse(image_url)
        bucket_name = 'sprayimages'
        s3_key = parsed_url.path.lstrip('/')
        try:
            # Delete the object from the S3 bucket
            s3.delete_object(Bucket=bucket_name, Key=s3_key)
        except Exception as e:
            # Log the error and continue (you can adjust this behavior as needed)
            print(f"Failed to delete {s3_key} from S3: {str(e)}")