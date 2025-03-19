from rest_framework import status, generics, permissions, mixins
from rest_framework.response import Response
from django.db.models import OuterRef, Exists, Q
from django_filters import rest_framework as filters
from utils.pagination import StandardPagination
from .serializers import BoulderSerializer, BoulderDetailSerializer
from ..circuit.serializers import CircuitSerializer
from .models import Boulder
from ..circuit.models import Circuit
from ..like.models import Like
from ..send.models import Send
from ..bookmark.models import Bookmark
from utils.filters import BoulderFilter
from rest_framework.request import Request
from mypy_boto3_s3 import S3Client
from urllib.parse import urlparse
from django.core.files.uploadedfile import UploadedFile
import boto3
import environ
env = environ.Env()
environ.Env.read_env()
s3: S3Client = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'), region_name='us-west-1')

class BoulderList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = BoulderFilter
    pagination_class = StandardPagination

    def get_queryset(self):
        """
        This method retrieves the queryset of boulders for a specific spraywall.
        It also annotates each boulder with user-specific flags like is_liked, is_bookmarked, etc.
        """
        spraywall_id = self.kwargs['spraywall_id']
        user_id = self.request.user.id
        # Check if the current person (user) has liked, bookmarked, and sent each boulder. 
        # Check if the current person put that particular boulder in any of their circuits.
        liked_subquery = Like.objects.select_related('person', 'boulder').filter(
            boulder=OuterRef('pk'),
            person=user_id
        )
        bookmarked_subquery = Bookmark.objects.select_related('person', 'boulder').filter(
            boulder=OuterRef('pk'),
            person=user_id
        )
        sent_subquery = Send.objects.select_related('person', 'boulder').filter(
            boulder=OuterRef('pk'),
            person=user_id
        )
        in_circuit_subquery = Circuit.objects.select_related('person', 'spraywall').filter(
            boulders=OuterRef('pk'),
            person=user_id
        )
        # Filter boulders by the spraywall. Annotate (adding more attributes) for booleans of 
        # whether or not the user liked, bookmarked, sent boulder or put the the particular boulder in a circuit.
        # select_related: reduces number of database queries when getting foreign keys. Everything is done on initial query
        # Will then be handed to filterset_class of BoulderFilter
        # Then to serializer_class
        # And finally to pagination_class
        return Boulder.objects.select_related(
                'spraywall', 'setter', 'first_ascensionist'
            ).filter(
                spraywall=spraywall_id
            ).filter(
                Q(publish=True) | Q(setter=user_id, publish=False) # published boulders or user's drafts
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery)
            ).distinct()
    
    def post(self, request: Request, *args, **kwargs):
        data = {}
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            print('No file uploaded or file not found in request.FILES.')
        if not isinstance(uploaded_file, UploadedFile):
            print('Invalid file object type.')
        # altWallImage is an optional upload so this will either get the alt wall file or return None.
        uploaded_alt_wall_file = request.FILES.get('altWallImage')
        name = request.data.get('name')
        description = request.data.get('description')
        publish = request.data.get('publish')
        matching = request.data.get('matching')
        feetFollowHands = request.data.get('feetFollowHands')
        kickboardOn = request.data.get('kickboardOn')
        width = request.data.get('width')
        height = request.data.get('height')
        setter = request.data.get('setter')
        spraywall = request.data.get('spraywall')
        data['url'] = uploaded_file
        data['name'] = name
        data['description'] = description
        data['publish'] = True if publish == 'true' else False
        data['matching'] = True if matching == 'true' else False
        data['feetFollowHands'] = True if feetFollowHands == 'true' else False
        data['kickboardOn'] = True if kickboardOn == 'true' else False
        data['width'] = width
        data['height'] = height
        data['setter'] = setter
        data['spraywall'] = spraywall
        data['altWallUrl'] = uploaded_alt_wall_file
        # _full_data is the private attribute holding request.data
        request._full_data = data
        return super().post(request, *args, **kwargs)
    
class BoulderDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Boulder.objects.all()
    serializer_class = BoulderDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        boulder_row = Boulder.objects.get(id=kwargs['pk'])
        # Delete boulder image from amazon s3
        self.delete_image_from_s3(boulder_row.image_url)
        # Delete the alternative spray wall image for the boulder if it exists.
        if boulder_row.alt_wall_image_url:
            self.delete_image_from_s3(boulder_row.alt_wall_image_url)
        return self.destroy(request, *args, **kwargs)
    
    @staticmethod
    def delete_image_from_s3(image_url: str):
        parsed_url = urlparse(image_url)
        s3_key = parsed_url.path.lstrip('/')
        # Delete the object from the S3 bucket
        s3.delete_object(Bucket=env('BUCKET'), Key=s3_key)

class BoulderInCircuit(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CircuitSerializer

    def post(self, request, *args, **kwargs):
        try:
            circuit = Circuit.objects.get(id=self.kwargs['circuit_id'], person=self.request.user.id)
            boulder = Boulder.objects.get(id=self.kwargs['boulder_id'])
            circuit.boulders.add(boulder)
            return Response({'detail': 'Boulder added to circuit'}, status=status.HTTP_200_OK)
        except Circuit.DoesNotExist:
            return Response({'detail': 'Circuit not found'}, status=status.HTTP_404_NOT_FOUND)
        except Boulder.DoesNotExist:
            return Response({'detail': 'Boulder not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        try:
            circuit = Circuit.objects.get(id=self.kwargs['circuit_id'], person=self.request.user.id)
            boulder = Boulder.objects.get(id=self.kwargs['boulder_id'])
            circuit.boulders.remove(boulder)
            return Response({'detail': 'Boulder removed from circuit'}, status=status.HTTP_200_OK)
        except Circuit.DoesNotExist:
            return Response({'detail': 'Circuit not found'}, status=status.HTTP_404_NOT_FOUND)
        except Boulder.DoesNotExist:
            return Response({'detail': 'Boulder not found'}, status=status.HTTP_404_NOT_FOUND)