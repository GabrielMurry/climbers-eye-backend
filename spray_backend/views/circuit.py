from spray_backend.utils.common_imports import *
from spray_backend.utils.circuit import *
from spray_backend.utils.profile import get_profile_quick_data
from spray_backend.utils.auth import *

@api_view(['GET', 'POST'])
def circuits(request, user_id, spraywall_id, boulder_id):
    if request.method == 'GET':
        # get all circuits associated to that particular user and spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        data = get_circuit_list_data(circuits, boulder_id)
        return Response(data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        # adding a new circuit (brand new circuits don't initially contain any boulders)
        circuit_serializer = CircuitSerializer(data=request.data, partial=True)
        if circuit_serializer.is_valid():
            circuit = circuit_serializer.save()
            person = Person.objects.get(id=user_id)
            spraywalls = get_all_spraywalls_data(person)
            profile_quick_data = get_profile_quick_data(person.id, spraywalls)
            data = {
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private,
                'profileData': profile_quick_data,
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            print(circuit_serializer.errors)

@api_view(['DELETE'])
def delete_circuit(request, user_id, spraywall_id, circuit_id):
    if request.method == 'DELETE':
        # deleting a user's particular circuit in a particular spraywall
        circuit_row = Circuit.objects.get(id=circuit_id, person=user_id, spraywall=spraywall_id)
        circuit_row.delete()
        person = Person.objects.get(id=user_id)
        spraywalls = get_all_spraywalls_data(person)
        profile_quick_data = get_profile_quick_data(person.id, spraywalls)
        data = {
            'profileData': profile_quick_data,
        }
        return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def filter_circuits(request, user_id, spraywall_id):
    if request.method == 'GET':
        # get all circuits associated to that particular user and spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        data = get_circuit_list_data(circuits)
        return Response(data, status=status.HTTP_200_OK)