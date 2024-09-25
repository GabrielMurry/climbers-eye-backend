# from climbers_eye.utils.common_imports import *
# from climbers_eye.utils.circuit import *
# from climbers_eye.utils.profile import get_profile_quick_data
# from climbers_eye.utils.auth import *
from rest_framework import status, generics, permissions, mixins
from climbers_eye_backend.models import Person, Boulder, Like, Send, Circuit, Bookmark
from climbers_eye_backend.serializers import circuit_serializers

class CircuitList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = circuit_serializers.CircuitSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        spraywall_id = self.kwargs['spraywall_id']
        return Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
    
class CircuitDetail(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Circuit.objects.all()
    serializer_class = circuit_serializers.CircuitSerializer

# @api_view(['GET'])
# def filter_circuits(request, user_id, spraywall_id):
#     if request.method == 'GET':
#         # get all circuits associated to that particular user and spraywall
#         circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
#         data = get_circuit_list_data(circuits)
#         return Response(data, status=status.HTTP_200_OK)