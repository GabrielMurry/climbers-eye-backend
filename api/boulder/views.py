from rest_framework import status, generics, permissions, mixins
from rest_framework.response import Response
from django.db.models import OuterRef, Exists, Q, Value
from django_filters.rest_framework import DjangoFilterBackend
from utils.pagination import CreatedCursorPagination
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
from utils.thumbnail import generate_thumbnail
from django.db.models.functions import Coalesce
from PIL import Image, ImageOps
from rest_framework.filters import OrderingFilter
from urllib.parse import urlparse
from django.core.files.uploadedfile import UploadedFile
import boto3
import environ
env = environ.Env()
environ.Env.read_env()
s3: S3Client = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'), region_name='us-west-1')

SORT_MAPPING = {
    'popular': '-sends_count',
    'newest': '-date_created',
    'oldest': 'date_created',
    'name': 'name',
    'grade': '-grade',
    'hardest': '-grade',
    'easiest': 'grade',
}

class BoulderList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BoulderFilter
    ordering_fields = {
        'grade':       ('grade', 'id'),        # tie-break on PK. Could have multiple of the same grade
        'sends_count': ('sends_count', 'id'),
        'date_created': ('date_created', 'id'),
    }
    ordering = ['sends_count', '-id']  # id is the tie breaker since sends_count and grade are not unique
    pagination_class = CreatedCursorPagination

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
        ordering_param = self.request.query_params.get('ordering')
        if ordering_param in SORT_MAPPING:
            # NOTE: must override query_params immutability
            self.request.query_params._mutable = True
            self.request.query_params['ordering'] = SORT_MAPPING[ordering_param]
            self.request.query_params._mutable = False
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
                is_in_circuit=Exists(in_circuit_subquery),
            ).distinct()
    
    @staticmethod
    def resize_image_to_720p(image: UploadedFile) -> Image:
        """
        Resizes an UploadedFile image to 720p (1280x720) using PIL.

        Args:
            image (UploadedFile): Image of UploadedFile type.
        """
        try:
            img = Image.open(image)
            img = ImageOps.exif_transpose(img)
            width, height = img.size

            # Calculate the new dimensions while maintaining aspect ratio
            if width / height > 1280 / 720:
                new_width = 1280
                new_height = int(height * (1280 / width))
            else:
                new_height = 720
                new_width = int(width * (720 / height))

            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            resized_img.save("resized_image.jpg", format="png", optimize=True, quality=85)
            return resized_img
        except FileNotFoundError:
            print(f"Error: Image file not found at {image}")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def post(self, request: Request, *args, **kwargs):
        data = {}
        uploaded_boulder_file = request.FILES.get('boulderImage')
        if not uploaded_boulder_file:
            print('No file uploaded or file not found in request.FILES.')
        if not isinstance(uploaded_boulder_file, UploadedFile):
            print('Invalid file object type.')
        # altWallImage is an optional upload so this will either get the alt wall file or return None.
        uploaded_alt_wall_file = request.FILES.get('altWallImage')
        thumbnail_uploaded_file = generate_thumbnail(uploaded_alt_wall_file, request.data.get('name'))
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
        data['url'] = uploaded_boulder_file
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
        data['altWallThumbnailUrl'] = thumbnail_uploaded_file
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