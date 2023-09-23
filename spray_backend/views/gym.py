from spray_backend.utils.common_imports import *
from spray_backend.utils.common_functions import *
from spray_backend.utils.gym import *

@api_view(['POST'])
def add_gym(request, user_id):
    if request.method == 'POST':
        gym_data = request.data.get('gym')
        spraywall_data = request.data.get('spraywall')

        gym_instance = create_gym(gym_data)
        spraywall_instance = create_spraywall(spraywall_data, gym_instance)
        update_person_data(user_id, gym_instance, spraywall_instance)

        return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
def query_gyms(request):
    if request.method == 'GET':
        # Convert search query to lowercase
        search_query = request.GET.get('search', '').lower()
        gyms = Gym.objects.filter(Q(name__icontains=search_query) | Q(location__icontains=search_query))
        data = []
        for gym in gyms:
            data.append(get_gym_data(gym))
        return Response({'data': data}, status=status.HTTP_200_OK)
    
@api_view(['PUT'])
def choose_gym(request, user_id, gym_id):
    if request.method == 'PUT':
        # updating person's default gym 
        person_data = {
            'gym': gym_id,
        }
        person = Person.objects.get(id=user_id)
        # update or add user's new default gym and spraywall
        person_serializer = PersonSerializer(instance=person, data=person_data, partial=True)
        if person_serializer.is_valid():
            person_instance = person_serializer.save()
            person_updated = Person.objects.get(id=person_instance.id)
            data = {
                'gym': get_gym_data(person_updated.gym),
                'spraywalls': get_spraywalls(gym_id),
            }
            return Response({'data': data}, status=status.HTTP_200_OK)
        else:
            print(person_serializer.errors)

@api_view(['POST'])
def edit_gym(request, gym_id):
    if request.method == 'POST':
        gym = Gym.objects.get(id=gym_id)
        gym_serializer = GymSerializer(instance=gym, data=request.data, partial=True)
        if gym_serializer.is_valid():
            gym_instance = gym_serializer.save() # Save the gym instance and get the saved object
            data = {
                'gym': get_gym_data(gym_instance)
            }
            return Response({'data': data}, status=status.HTTP_200_OK)
        else:
            print(gym_serializer.errors)

@api_view(['DELETE'])
def delete_gym(request, gym_id):
    if request.method == 'DELETE':
        gym_row = Gym.objects.get(id=gym_id)
        delete_gym_data(gym_row)
        return Response(status=status.HTTP_200_OK)