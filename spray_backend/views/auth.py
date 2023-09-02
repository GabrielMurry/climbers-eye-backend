from . import *

@api_view(['GET'])
def csrf_token_view(request):
    if request.method == 'GET':
        return Response({'csrfToken': get_token(request)})

@api_view(['POST'])
def signup_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.data)
        if form.is_valid():
            form.save()
            person_serializer = PersonSerializer(data=request.data)
            if person_serializer.is_valid():
                person_instance = person_serializer.save()
                username = request.data.get('username')
                user = {
                    'id': person_instance.id,
                    'username': username
                }
                data = {
                    'user': user
                }
                return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
            else:
                print(person_serializer.errors)
        else:
            print(form.errors)

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            person = Person.objects.get(username=username)
            data = {}
            user = {
                'id': person.id,
                'username': username,
                'name': person.name,
                'email': person.email,
            }
            if person.gym_id:
                gym_id = person.gym_id
                spraywalls = get_spraywalls(gym_id)
                gym = {
                    'id': person.gym_id,
                    'name': person.gym.name,
                    'location': person.gym.location,
                    'type': person.gym.type,
                }
                headshot_image = {
                    'url': person.headshot_image_url if person.headshot_image_url else None,
                    'width':  person.headshot_image_width, 
                    'height': person.headshot_image_height, 
                }
                data = {
                    'user': user, 
                    'gym': gym,
                    'spraywalls': spraywalls, 
                    'headshotImage': headshot_image,
                }
            else:
                headshot_image = {
                    'url': person.headshot_image_url if person.headshot_image_url else None,
                    'width': person.headshot_image_width,
                    'height': person.headshot_image_height,
                }
                data = {
                    'user': user, 
                    'headshotImage': headshot_image,
                }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        # else:
        #     print('hi')
        #     return Response({'data': 'Username or password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
def logout_user(request):
    logout(request)
    return Response('logged out')