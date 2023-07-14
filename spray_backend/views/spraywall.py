from . import *

@api_view(['GET', 'POST'])
def spraywall(request):
    if request.method == 'POST':
        serializer = SprayWallSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # pass data back in response
            return Response('hi')
    if request.method == 'GET':
        queryset = SprayWall.objects.filter(id=2)
        serializer = SprayWallSerializer(queryset, many=True)
        return Response(serializer.data)
    
@api_view(['GET'])
def queried_gym_spraywall(request, gym_id):
    if request.method == 'GET':
        # get gym's spraywall image, width, and height to display on bottom sheet in map screen when user clicks on gym card
        spraywalls = get_spraywalls(gym_id)
        data = {
            'spraywalls': spraywalls
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def add_new_spraywall(request, gym_id):
    if request.method == 'POST':
        # Add New Spray Wall
        spraywall = request.data
        image_url = s3_image_url(spraywall['image_data'])
        spraywall_data = {
            'name': spraywall['name'],
            'spraywall_image_url': image_url,
            'spraywall_image_width': spraywall['image_width'],
            'spraywall_image_height': spraywall['image_height'],
            'gym': gym_id,
        }
        spraywall_serializer = SprayWallSerializer(data=spraywall_data)
        if spraywall_serializer.is_valid():
            spraywall_serializer.save()
            spraywalls = get_spraywalls(gym_id)
            data = {
                'spraywalls': spraywalls
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(spraywall_serializer.errors)

@api_view(['DELETE'])
def delete_spraywall(request, spraywall_id):
    if request.method == 'DELETE':
        # grab spraywall row
        spraywall_row = SprayWall.objects.get(id=spraywall_id)
        # delete spraywall image from amazon s3
        delete_image_from_s3(spraywall_row.spraywall_image_url)
        # delete spraywall row from postgresql 
        spraywall_row.delete()
        gym_id = spraywall_row.gym_id
        spraywalls = get_spraywalls(gym_id)
        data = {
            'spraywalls': spraywalls
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def edit_spraywall(request, spraywall_id):
    if request.method == 'POST':
        spraywall = SprayWall.objects.get(id=spraywall_id)
        spraywall_serializer = SprayWallSerializer(instance=spraywall, data=request.data, partial=True)
        if spraywall_serializer.is_valid():
            spraywall_instance = spraywall_serializer.save() # Save the gym instance and get the saved object
            gym_id = spraywall_instance.gym_id
            spraywalls = get_spraywalls(gym_id)
            data = {
                'spraywalls': spraywalls
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(spraywall_serializer.errors)