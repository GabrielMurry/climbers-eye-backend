from rest_framework import generics, permissions, mixins
from .serializers import BookmarkSerializer
from .models import Bookmark

class BookmarkBoulder(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookmarkSerializer

    def get_object(self):
        """
        Override to apply multiple filter criteria based on the request to get our Bookmark object.
        """
        return Bookmark.objects.filter(boulder=self.kwargs['boulder_id'], person=self.kwargs['user_id'])

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)