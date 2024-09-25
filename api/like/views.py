from rest_framework import generics, permissions, mixins
from .serializers import LikeSerializer
from .models import Like

class LikeBoulder(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LikeSerializer

    def get_object(self):
        """
        Override to apply multiple filter criteria based on the request to get our Like object.
        """
        return Like.objects.filter(boulder=self.kwargs['boulder_id'], person=self.kwargs['user_id'])

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)