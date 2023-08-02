from . import *

@api_view(['POST'])
def add_gym(request, user_id):
    if request.method == 'POST':
        # Add Gym
        gym = request.data.get('gym')
        gym_data = {
            'name': gym['name'],
            'location': gym['location'],
            'type': gym['type'],
        }
        gym_serializer = GymSerializer(data=gym_data)
        if gym_serializer.is_valid():
            gym_instance = gym_serializer.save() # Save the gym instance and get the saved object --> need the recently created gym's ID!
            # Add Spray Wall
            spraywall = request.data.get('spraywall')
            image_url = s3_image_url(spraywall['image_data'])
            spraywall_data = {
                'name': spraywall['name'],
                'spraywall_image_url': image_url,
                'spraywall_image_width': spraywall['image_width'],
                'spraywall_image_height': spraywall['image_height'],
                'gym': gym_instance.id,
            }
            spraywall_serializer = SprayWallSerializer(data=spraywall_data)
            if spraywall_serializer.is_valid():
                spraywall_instance = spraywall_serializer.save()
                # Update Person data: person's gym_id foreign key and spraywall_id foreign key --> signifies person's default Gym and Wall
                person = Person.objects.get(id=user_id)
                person_data = {
                    'gym': gym_instance.id,
                    'spraywall': spraywall_instance.id
                }
                person_serializer = PersonSerializer(instance=person, data=person_data, partial=True) # partial=True allows for partial updates
                if person_serializer.is_valid():
                    person_serializer.save()
                    return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
                else:
                    print(person_serializer.errors)
            else:
                print(spraywall_serializer.errors)
        else:
            print(gym_serializer.errors)

@api_view(['GET'])
def query_gyms(request):
    if request.method == 'GET':
        # Convert search query to lowercase
        search_query = request.GET.get('search', '').lower()
        gyms = Gym.objects.filter(Q(name__icontains=search_query) | Q(location__icontains=search_query))
         # get everything except image data, image width, image height --> image data takes very long to load especially when grabbing every single boulder
        data = []
        for gym in gyms:
            data.append({
                'id': gym.id, 
                'name': gym.name, 
                'location': gym.location,
            })
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
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
            gym = {
                'id': gym_id,
                'name': person_updated.gym.name,
                'location': person_updated.gym.location,
                'type': person_updated.gym.type,
            }
            spraywalls = get_spraywalls(gym_id)
            data = {
                'gym': gym,
                'spraywalls': spraywalls,
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(person_serializer.errors)

@api_view(['POST'])
def edit_gym(request, gym_id):
    if request.method == 'POST':
        gym = Gym.objects.get(id=gym_id)
        gym_serializer = GymSerializer(instance=gym, data=request.data, partial=True)
        if gym_serializer.is_valid():
            gym_instance = gym_serializer.save() # Save the gym instance and get the saved object
            gym = {
                'id': gym_instance.id,
                'name': gym_instance.name,
                'location': gym_instance.location,
                'type': gym_instance.type,
            }
            data = {
                'gym': gym
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(gym_serializer.errors)

@api_view(['DELETE'])
def delete_gym(request, gym_id):
    if request.method == 'DELETE':
        # get gym row
        gym_row = Gym.objects.get(id=gym_id)
        # get all spray walls associated with specific gym
        spraywalls = SprayWall.objects.filter(gym=gym_id)
        for spraywall in spraywalls:
            # get all boulders associated with specific spray wall
            boulders = Boulder.objects.filter(spraywall=spraywall.id)
            for boulder in boulders:
                # delete s3 image boulder
                delete_image_from_s3(boulder.boulder_image_url)
                # delete boulder
                boulder.delete()
            # when all boulders associated with specific spray wall are deleted, then delete spray wall s3 image
            delete_image_from_s3(spraywall.spraywall_image_url)
            # delete spray wall
            spraywall.delete()
        # when all spray walls associated with specific gym are deleted, then delete gym
        gym_row.delete()
        # Return a success response
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)