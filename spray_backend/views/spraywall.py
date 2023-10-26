from spray_backend.utils.common_imports import *
from spray_backend.utils.common_functions import *
from spray_backend.utils.spraywall import *


@api_view(['GET'])
def queried_gym_spraywall(request, gym_id):
    if request.method == 'GET':
        # get gym's spraywall image, width, and height to display on bottom sheet in map screen when user clicks on gym card
        spraywalls = get_spraywalls(gym_id)
        data = {
            'spraywalls': spraywalls
        }
        return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
def add_new_spraywall(request, gym_id):
    if request.method == 'POST':
        spraywall = request.data
        create_spraywall(spraywall, gym_id)
        data = {
            'spraywalls': get_spraywalls(gym_id)
        }
        return Response(data, status=status.HTTP_200_OK)


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
        return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
def edit_spraywall(request, spraywall_id):
    if request.method == 'POST':
        spraywall = SprayWall.objects.get(id=spraywall_id)
        spraywall_serializer = SprayWallSerializer(
            instance=spraywall, data=request.data, partial=True)
        if spraywall_serializer.is_valid():
            # Save the gym instance and get the saved object
            spraywall_instance = spraywall_serializer.save()
            gym_id = spraywall_instance.gym_id
            spraywalls = get_spraywalls(gym_id)
            data = {
                'spraywalls': spraywalls
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            print(spraywall_serializer.errors)
