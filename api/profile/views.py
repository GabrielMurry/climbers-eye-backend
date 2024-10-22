from rest_framework import generics, permissions
from django.db.models import OuterRef, Exists, Subquery, Count, F
from ..like.models import Like
from ..bookmark.models import Bookmark
from ..send.models import Send
from ..circuit.models import Circuit
from ..boulder.models import Boulder
from ..boulder.serializers import BoulderSerializer
from .serializers import LogbookSerializer
from utils.pagination import StandardPagination
from utils.constants import grade_labels
    
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

        # Subquery to get the send date
        send_date_subquery = Send.objects.filter(
            person=user_id,
            boulder=OuterRef('pk')
        ).values('date_created')[:1]

        return Boulder.objects.filter(
                send__person=user_id, send__boulder__spraywall=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery),
                send_date=Subquery(send_date_subquery)
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
                    grade_chart.append({grade: grade_count_dict[grade]})
                else:
                    grade_chart.append({grade: 0})

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

