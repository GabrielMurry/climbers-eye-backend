from . import * 

@api_view(['GET', 'POST'])
def circuits(request, user_id, spraywall_id, boulder_id):
    if request.method == 'GET':
        # get all circuits associated to that particular user and spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        data = []
        for circuit in circuits:
            boulder_is_in_circuit = circuit.boulders.filter(pk=boulder_id).exists()
            data.append({
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private,
                'isSelected': boulder_is_in_circuit
            })
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    if request.method == 'POST':
        # adding a new circuit (brand new circuits don't initially contain any boulders)
        circuit_serializer = CircuitSerializer(data=request.data, partial=True)
        if circuit_serializer.is_valid():
            circuit = circuit_serializer.save()
            data = {
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(circuit_serializer.errors)

@api_view(['DELETE'])
def delete_circuit(request, user_id, spraywall_id, circuit_id):
    if request.method == 'DELETE':
        # deleting a user's particular circuit in a particular spraywall
        circuit_row = Circuit.objects.get(id=circuit_id, person=user_id, spraywall=spraywall_id)
        circuit_row.delete()
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)

@api_view(['GET'])
def filter_circuits(request, user_id, spraywall_id):
    if request.method == 'GET':
        # get all circuits associated to that particular user and spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        data = []
        for circuit in circuits:
            data.append({
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private,
            })
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)