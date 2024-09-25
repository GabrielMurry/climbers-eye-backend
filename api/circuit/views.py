from rest_framework import generics, permissions
from .models import Circuit
from .serializers import CircuitSerializer

class CircuitList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CircuitSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        spraywall_id = self.kwargs['spraywall_id']
        return Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
    
class CircuitDetail(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Circuit.objects.all()
    serializer_class = CircuitSerializer