from rest_framework import generics, permissions
from django.db.models import OuterRef, Exists, Q
from ..like.models import Like
from ..bookmark.models import Bookmark
from ..send.models import Send
from ..circuit.models import Circuit
from ..boulder.models import Boulder
from ..boulder.serializers import BoulderSerializer

# class SpraywallList(generics.ListCreateAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SprayWallSerializer

#     def get_queryset(self):
#         gym_id = self.kwargs['gym_id']
#         return SprayWall.objects.filter(gym=gym_id)
    
class LogbookList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoulderSerializer

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
                send__person=user_id, send__boulder__spraywall=spraywall_id
            ).annotate(
                is_liked=Exists(liked_subquery),
                is_bookmarked=Exists(bookmarked_subquery),
                is_sent=Exists(sent_subquery),
                is_in_circuit=Exists(in_circuit_subquery)
            ).order_by('-send__date_created')

