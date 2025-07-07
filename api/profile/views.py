from rest_framework import generics, permissions, status
from django.db.models import OuterRef, Exists, Subquery, Count, F
from rest_framework.response import Response
from urllib.parse import urlparse
from ..like.models import Like
from ..bookmark.models import Bookmark
from ..send.models import Send
from ..circuit.models import Circuit
from ..boulder.models import Boulder
from ..boulder.serializers import BoulderSerializer
from utils.pagination import CreatedCursorPagination
from ..user.serializers import PersonSerializer
from ..user.models import Person
from .serializers import LogbookSerializer
from utils.pagination import StandardPagination
from utils.constants import grade_labels
import boto3, environ
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

class LogbookCursorPagination(CreatedCursorPagination):
    ordering = ('-date_created', '-id')
    
class LogbookList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogbookSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        spraywall_id = self.kwargs['spraywall_id']
        user_id = self.request.user.id

        liked_subquery = Like.objects.select_related('person', 'boulder').filter(
            boulder=OuterRef('pk'),
            person=user_id
        )
        bookmarked_subquery = Bookmark.objects.select_related('person', 'boulder').filter(
            boulder=OuterRef('pk'),
            person=user_id
        )
        sent_subquery = Send.objects.select_related('person', 'boulder', 'date_created').filter(
            boulder=OuterRef('pk'),
            person=user_id
        )
        in_circuit_subquery = Circuit.objects.select_related('person', 'spraywall').filter(
            boulders=OuterRef('pk'),
            person=user_id
        )

        return Boulder.objects.filter(
                send__person=user_id, send__boulder__spraywall=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery),
                send_date=Subquery(sent_subquery.values('date_created')[:1])
            ).order_by('-send__date_created')

    def list(self, request, *args, **kwargs):
        # Get the page number from the request query params
        page = request.query_params.get('page', 1)

        # Call the default list method to get the paginated response
        response = super().list(request, *args, **kwargs)

        # Only calculate and add grade chart data if this is the first page
        if page == '1':
            spraywall_id = self.kwargs['spraywall_id']
            user_id = self.request.user.id

            # Aggregate send counts by grade
            grade_counts = Send.objects.filter(
                person=user_id,
                boulder__spraywall_id=spraywall_id
            ).values(grade=F('boulder__grade')).annotate(count=Count('id')).order_by('grade')

            grade_chart = []

            # Create a dictionary from grade_counts for faster lookup by grade.
            # The grade in grade_counts is in int form (type). Convert to readable char form.
            grade_count_dict = {grade_labels[item['grade']]: item['count'] for item in grade_counts}

            # Loop through all the possible grades and append the count or 0 if not present
            for grade in grade_labels:
                if grade in grade_count_dict:
                    grade_chart.append({'label': grade, 'value': grade_count_dict[grade]})
                else:
                    grade_chart.append({'label': grade, 'value': 0})

            # Add chart data to the response
            response.data['grade_chart'] = grade_chart
        else:
            # If not page 1, exclude the grade_chart data from the response
            response.data['grade_chart'] = None

        return response
    
class LikeList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        spraywall_id = self.kwargs['spraywall_id']
        user_id = self.request.user.id

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
        return Boulder.objects.filter(
                like__person=user_id, like__boulder__spraywall=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery)
            ).order_by('-like__date_created')
    
class BookmarkList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        spraywall_id = self.kwargs['spraywall_id']
        user_id = self.request.user.id

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
        return Boulder.objects.filter(
                bookmark__person=user_id, bookmark__boulder__spraywall=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery)
            ).order_by('-bookmark__date_created')
    
class CreationList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        spraywall_id = self.kwargs['spraywall_id']
        user_id = self.request.user.id

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
        return Boulder.objects.filter(
                setter=user_id, spraywall=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery)
            ).distinct().order_by('-date_created')

class ProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PersonSerializer

    def get_object(self):
        user_id = self.request.user.id
        return Person.objects.get(id=user_id)
    
    def patch(self, request, *args, **kwargs):
        user_instance = self.get_object()
        # Check if 'profilePicUrl' is in the request data
        if 'profilePicUrl' in request.data:
            self.delete_image_from_s3(user_instance.image_url)
            data = {}
            data['profilePicUrl'] = request.data['profilePicUrl']
            data['profilePicWidth'] = request.data['profilePicWidth']
            data['profilePicHeight'] = request.data['profilePicHeight']
            # _full_data is the private attribute holding request.data
            request._full_data = data
        return super().patch(request, *args, **kwargs)
    
    def delete_image_from_s3(self, image_url):
        try:
            parsed_url = urlparse(image_url)
            bucket_name = 'sprayimages'
            s3_key = parsed_url.path.lstrip('/')
            # Delete the object from the S3 bucket
            s3.delete_object(Bucket=bucket_name, Key=s3_key)
        except Exception as e:
            return Response({"error": f"Failed to delete image from S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)