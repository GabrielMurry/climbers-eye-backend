from rest_framework.pagination import PageNumberPagination
from rest_framework import status, generics, permissions, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import OuterRef, Exists, Q
from django_filters import rest_framework as filters
from .serializers import BoulderSerializer, BoulderDetailSerializer
from ..circuit.serializers import CircuitSerializer
from .models import Boulder
from ..circuit.models import Circuit
from ..like.models import Like
from ..send.models import Send
from ..bookmark.models import Bookmark
from utils.filters import BoulderFilter
from PIL import Image, ImageEnhance
from io import BytesIO
import base64
from urllib.parse import urlparse
import boto3
import environ
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10

class BoulderList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = BoulderFilter
    pagination_class = StandardResultsSetPagination

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
            ).distinct() # before pagination, ensure only distinct boulders are returned. - Avoids duplicates that may have arose from annotate or select_related
    
class BoulderDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Boulder.objects.all()
    serializer_class = BoulderDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        boulder_row = Boulder.objects.get(id=kwargs['pk'])
        # delete boulder image from amazon s3
        self.delete_image_from_s3(boulder_row.image_url)
        return self.destroy(request, *args, **kwargs)
    
    @staticmethod
    def delete_image_from_s3(self, image_url: str):
        parsed_url = urlparse(image_url)
        bucket_name = 'sprayimages'
        s3_key = parsed_url.path.lstrip('/')
        # Delete the object from the S3 bucket
        s3.delete_object(Bucket=bucket_name, Key=s3_key)

class CompositeBoulderImage(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        manipulated_data = self.composite(request.data)
        # Return the manipulated data
        return Response(manipulated_data, status=status.HTTP_200_OK)

    def composite(self, data):
        drawing_image, photo_image = self.base64_string_to_image(data['drawing'], data['photo'])
        drawing_image = self.increase_drawing_opacity(drawing_image)
        drawing_image = self.mask_drawing(drawing_image, photo_image)
        result = self.combine_images(drawing_image, photo_image)
        result_uri = 'data:image/png;base64,' + self.image_to_base64_string(result)
        return { 'uri': result_uri }
    
    def base64_string_to_image(self, drawing, photo):
        drawing_image = Image.open(BytesIO(base64.b64decode(drawing)))
        photo_image = Image.open(BytesIO(base64.b64decode(photo)))
        return drawing_image, photo_image
    
    def increase_drawing_opacity(self, drawing_image):
        # increase opacity of drawings, but NOT the transparent background
        # Split the image into channels 
        r, g, b, a = drawing_image.split()
        # Increase the opacity of the alpha channel
        # Multiplication - transparent alpha is 0 so it will stay 0
        # Multiply by 2.5 since we want to increase it by 2.5 to get 255. Our original opacity is 0.4, multiply that by 2.5 and we get 1
        a = a.point(lambda x: x * 2)
        # Merge the channels back into an RGBA image
        return Image.merge('RGBA', (r, g, b, a))
    
    def mask_drawing(self, drawing_image, photo_image):
        # Create a blank white mask, same size, and gray-scaled (mode 'L')
        mask = Image.new("L", drawing_image.size, 'WHITE')
        # Paste our drawing over new blank mask, masking the drawings with the drawings themselves
        mask.paste(drawing_image, mask=drawing_image)
        # Cut out the photo where we drew using our drawing mask
        drawing_image = Image.composite(drawing_image, photo_image, mask)
        return drawing_image
    
    def combine_images(self, drawing_image, photo_image):
        # gray-scale photo image, but before converting to 'L' mode, grab the alpha channel
        # converting to 'L' mode (Luminance) gray-scales image efficiently through a single 8-bit channel per pixel, rather than RGBA which provides 4 x 8-bit channels per pixel
        alpha_channel  = photo_image.getchannel('A')
        gray_channels = photo_image.convert('L')
        # convert back to RGBA but merge the gray channel values as 'RGB' and the original alpha channel for 'A', all as a tuple.
        photo_image_result = Image.merge('RGBA', (gray_channels, gray_channels, gray_channels, alpha_channel))
        # darken photo image background before alpha compositing the images together
        brightnessLevel = ImageEnhance.Brightness(photo_image_result)
        # factor > 1 brightens. factor < 1 darkens
        factor = 0.4
        photo_image_result = brightnessLevel.enhance(factor)
        # alpha composite to place drawing image on top of manipulated photo image
        photo_image_result.alpha_composite(drawing_image)
        return photo_image_result
    
    def image_to_base64_string(self, result):
        buffered = BytesIO()
        result.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

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