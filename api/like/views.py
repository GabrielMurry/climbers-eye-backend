from rest_framework import generics, permissions, mixins
from django.db.models import OuterRef, Subquery, Exists
from .serializers import LikeSerializer
from ..bookmark.models import Bookmark
from ..send.models import Send
from ..circuit.models import Circuit
from .models import Like
from utils.pagination import CreatedCursorPagination
from ..boulder.models import Boulder
from ..boulder.serializers import BoulderSerializer

class LikeCursorPagination(CreatedCursorPagination):
    ordering = ('-like_date', '-id')

class LikeList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer
    pagination_class = LikeCursorPagination

    def get_queryset(self):
        spraywall_id = self.kwargs['spraywall_id']
        user_id = self.request.user.id

        liked_subquery = Like.objects.select_related('person', 'boulder', 'date_created').filter(
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
                like__person=user_id, spraywall_id=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery),
                like_date=Subquery(liked_subquery.values('date_created')[:1])
            )
    
    # def get_queryset(self):
    #     spraywall_id = self.kwargs['spraywall_id']
    #     user_id = self.request.user.id

    #     liked_subquery = Like.objects.select_related('person', 'boulder').filter(
    #         boulder=OuterRef('pk'),
    #         person=user_id
    #     )
    #     bookmarked_subquery = Bookmark.objects.select_related('person', 'boulder').filter(
    #         boulder=OuterRef('pk'),
    #         person=user_id
    #     )
    #     sent_subquery = Send.objects.select_related('person', 'boulder', 'date_created').filter(
    #         boulder=OuterRef('pk'),
    #         person=user_id
    #     )
    #     in_circuit_subquery = Circuit.objects.select_related('person', 'spraywall').filter(
    #         boulders=OuterRef('pk'),
    #         person=user_id
    #     )

    #     # Subquery to get the like date
    #     like_date_subquery = Like.objects.filter(
    #         person=user_id,
    #         boulder=OuterRef('pk')
    #     ).values('date_created')[:1]

    #     return Boulder.objects.filter(
    #             like__person=user_id, send__boulder__spraywall=spraywall_id
    #         ).annotate(
    #             is_liked=Exists(liked_subquery),
    #             is_bookmarked=Exists(bookmarked_subquery),
    #             is_sent=Exists(sent_subquery),
    #             is_in_circuit=Exists(in_circuit_subquery),
    #             like_date=Subquery(like_date_subquery)
    #         ).exclude(like_date=None)

class LikeBoulder(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LikeSerializer

    def get_object(self):
        """
        Override to apply multiple filter criteria based on the request to get our Like object.
        """
        return Like.objects.filter(boulder=self.kwargs['boulder_id'], person=self.request.user.id)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)