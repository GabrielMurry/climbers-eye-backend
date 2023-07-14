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
                    'name': username
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
            if person.gym_id:
                gym_id = person.gym_id
                spraywalls = get_spraywalls(gym_id)
                user = {
                    'id': person.id,
                    'name': username
                }
                gym = {
                    'id': person.gym_id,
                    'name': person.gym.name,
                    'location': person.gym.location,
                    'type': person.gym.type,
                }
                data = {
                    'user': user, 
                    'gym': gym,
                    'spraywalls': spraywalls, 
                    'headshotImageUri': "data:image/png;base64," + person.headshot_image_url if person.headshot_image_url else None, 
                    'headshotImageWidth': person.headshot_image_width, 
                    'headshotImageHeight': person.headshot_image_height, 
                    'bannerImageUri': "data:image/png;base64," + person.banner_image_url if person.banner_image_url else None, 
                    'bannerImageWidth': person.banner_image_width, 
                    'bannerImageHeight': person.banner_image_height
                }
            else:
                data = {
                    'userID': person.id, 
                    'headshotImageUri': "data:image/png;base64," + person.headshot_image_data, 
                    'headshotImageWidth': person.headshot_image_width, 
                    'headshotImageHeight': person.headshot_image_height, 
                    'bannerImageUri': "data:image/png;base64," + person.banner_image_data if person.banner_image_data else None, 
                    'bannerImageWidth': person.banner_image_width, 
                    'bannerImageHeight': person.banner_image_height
                }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            return Response('Username or password is incorrect')
        
@api_view(['GET'])
def logout_user(request):
    logout(request)
    return Response('logged out')