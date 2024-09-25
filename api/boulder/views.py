import copy
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, generics, permissions, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, OuterRef, Exists, Q
from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404
from climbers_eye_backend.serializers import bookmark_serializers, boulder_serializers, circuit_serializers, gym_serializers, like_serializers, send_serializers, spraywall_serializers, user_serializers
from climbers_eye_backend.models import Person, Boulder, Like, Send, Circuit, Bookmark
from climbers_eye_backend.filters import BoulderFilter
from ...utils.constants import grade_labels
from decimal import Decimal, ROUND_HALF_UP
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
    serializer_class = boulder_serializers.BoulderSerializer
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
    serializer_class = boulder_serializers.BoulderDetailSerializer

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


class LikeBoulder(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = like_serializers.LikeSerializer

    def get_object(self):
        """
        Override to apply multiple filter criteria based on the request to get our Like object.
        """
        return Like.objects.filter(boulder=self.kwargs['boulder_id'], person=self.kwargs['user_id'])

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
class BookmarkBoulder(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = bookmark_serializers.BookmarkSerializer

    def get_object(self):
        """
        Override to apply multiple filter criteria based on the request to get our Bookmark object.
        """
        return Bookmark.objects.filter(boulder=self.kwargs['boulder_id'], person=self.kwargs['user_id'])

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
class SendList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = send_serializers.SendList

    def get_object(self):
        return get_object_or_404(Boulder, id=self.kwargs['boulder_id'])
    
    @staticmethod
    def grade_mode(self, boulder, suggested_grade) -> int:
        """
        Calculate the boulder grade mode from every send of this boulder including the new suggested grade.
        If mode lands in between two grades, return either grade. We want to find the grade consensus.

        Args:
            boulder: Boulder
            suggested_grade: str

        Returns:
            grade: int. Returns most common grade as type int.
        """
        # convert given grade argument to its index counterpart if the grade given is the human readable grade string
        if isinstance(suggested_grade, str):
            suggested_grade: int = grade_labels.index(suggested_grade)
        # Aggregate suggested grades and get the most common one
        suggested_grade_counts_queryset = (
            Send.objects
            .filter(boulder=boulder.id)
            .values('suggested_grade')
            .annotate(count=Count('suggested_grade'))
            .order_by('-count')
        )
        # Convert the queryset to a dictionary with grades as keys and their counts as values
        suggested_grade_counts: dict[int, int] = {item['suggested_grade']: item['count'] for item in suggested_grade_counts_queryset}
        # Manually include the passed grade in the count
        if suggested_grade in suggested_grade_counts:
            suggested_grade_counts[suggested_grade] += 1
        else:
            suggested_grade_counts[suggested_grade] = 1
        # Determine the most common grade including the passed grade
        most_common_grade: int = max(suggested_grade_counts, key=suggested_grade_counts.get)
        return most_common_grade
    
    @staticmethod
    def quality_mean(self, current_mean_score, num_existing_scores, new_score) -> Decimal:
        """
        Calculates new quality rating mean after adding user's new quality rating score.
        If the current mean score is None, then make it a 0 of type Decimal.

        Args:
        current_mean_score = current mean percentage of all scores.
        num_existing_scores = number of existing scores before adding the new score.
        new_score = user's quality rating score to be included in the mean.

        Returns:
        Return new quality rating mean of type Decimal
        """
        if current_mean_score is None:
            current_mean_score = Decimal(0)
        return ((num_existing_scores * current_mean_score) + new_score) / (num_existing_scores + 1)
  
    def post(self, request, *args, **kwargs):
        boulder = self.get_object()
        current_send_count = boulder.sends_count
        boulder.sends_count = current_send_count + 1
        boulder.grade = self.grade_mode(boulder, request.data.get('suggestedGrade'))
        boulder.quality = self.quality_mean(boulder.quality, current_send_count, request.data.get('quality'))
        if boulder.first_ascensionist is None:
            user_instance = Person.objects.get(id=self.request.user.id)
            boulder.first_ascensionist = user_instance
        boulder.save()
        return self.create(request, *args, **kwargs)
    
class SendDetail(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = send_serializers.SendDetail

    def get_object(self):
        return get_object_or_404(Send, id=self.kwargs['pk'])

    @staticmethod
    def grade_mode(self, boulder, send_id) -> int:
        """
        Calculate the boulder grade mode from every send of this boulder excluding the send from which the user wants to delete.
        If mode lands in between two grades, return either grade. We want to find the grade consensus.

        Args:
            boulder: Boulder
            send_id: int

        Returns:
            grade: int. Returns most common grade as type int.
        """
        # Aggregate suggested grades and get the most common one
        suggested_grade_counts_queryset = (
            Send.objects
            .filter(boulder=boulder.id)
            .exclude(id=send_id)  # Exclude the specific send object with send_id
            .values('suggested_grade')
            .annotate(count=Count('suggested_grade'))
            .order_by('-count')
        )
        # Convert the queryset to a dictionary with grades as keys and their counts as values
        suggested_grade_counts: dict[int, int] = {item['suggested_grade']: item['count'] for item in suggested_grade_counts_queryset}
        # Determine the most common grade including the passed grade
        most_common_grade: int = max(suggested_grade_counts, key=suggested_grade_counts.get)
        return most_common_grade
    
    @staticmethod
    def quality_mean(self, current_mean_score, num_existing_scores, remove_score) -> Decimal | None:
        """
        Calculates new quality rating mean after removing user's quality rating score.

        Args:
        current_mean_score = current mean percentage of all scores.
        num_existing_scores = number of existing scores before removing the score.
        remove_score = user's quality rating score to be removed

        Returns:
        If the number of existing scores is 0 after removing the score, return None.
        Else return new quality rating mean of type Decimal
        """
        if num_existing_scores - 1 == 0:
            return None
        else:
            return ((num_existing_scores * current_mean_score) - remove_score) / (num_existing_scores - 1)

    def delete(self, request, *args, **kwargs):
        send_instance = self.get_object()  # Get the send object
        boulder = send_instance.boulder
        sends_count = boulder.sends_count
        current_send_count = boulder.sends_count
        boulder.sends_count = current_send_count - 1
        boulder.grade = self.grade_mode(boulder, self.kwargs['pk'])
        boulder.quality = self.quality_mean(boulder.quality, current_send_count, send_instance.quality)
        if boulder.first_ascensionist:
            if sends_count == 1 and boulder.first_ascensionist.id is self.request.user.id:
                boulder.first_ascensionist = None
        boulder.save()
        return self.destroy(request, *args, **kwargs)


    
class BoulderInCircuit(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = circuit_serializers.CircuitSerializer

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