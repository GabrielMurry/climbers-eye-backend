from spray_backend.utils.profile import *
from spray_backend.utils.common_functions import *
from spray_backend.utils.common_imports import *
from spray_backend.utils.constants import boulders_section_quick_data_template, stats_section_quick_data_template

@api_view(['GET'])
def profile_quick_data(request, user_id, spraywall_id):
    if request.method == 'GET':
        # get copy of boulders section quick data template
        boulders_section_quick_data = copy.deepcopy(boulders_section_quick_data_template)
        # logbook
        sent_boulders = Boulder.objects.filter(send__person=user_id, spraywall=spraywall_id)
        boulders_section_quick_data['Logbook'] = get_logbook_quick_data(sent_boulders)
        # creations
        boulders = Boulder.objects.filter(spraywall=spraywall_id, setter_person=user_id)
        boulders_section_quick_data['Creations'] = get_creations_quick_data(boulders)
        # likes count
        boulders_section_quick_data['Likes'] = get_likes_quick_data(user_id, spraywall_id)
        # bookmarks count
        boulders_section_quick_data['Bookmarks'] = get_bookmarks_quick_data(user_id, spraywall_id)

        # get copy of stats section quick data template
        stats_section_quick_data = copy.deepcopy(stats_section_quick_data_template)
        stats_section_quick_data['Top Grade'] = get_top_grade_quick_data(sent_boulders)
        stats_section_quick_data['Flashes'] = get_flashes_quick_data(sent_boulders)
        data = {
            'bouldersSectionQuickData': boulders_section_quick_data,
            'statsSectionQuickData': stats_section_quick_data,
        }
        return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_user_circuits(request, user_id, spraywall_id):
    if request.method == 'GET':
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        circuits_data = []
        for circuit in circuits:
            # retrieving all boulder data in particular circuit
            boulders = circuit.boulders.all()
            boulder_data = []
            for boulder in boulders:
                boulder_data.append(get_boulder_data(boulder, user_id))
            # putting boulder data inside circuits data
            circuits_data.append({
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private,
                'boulderData': boulder_data,
            })
        data = {
            'circuitsData': circuits_data,
        }
        return Response(data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def add_profile_banner_image(request, user_id):
    if request.method == 'POST':
        person = Person.objects.get(id=user_id)
        person_serializer = PersonSerializer(instance=person, data=request.data, partial=True)
        if person_serializer.is_valid():
            person_serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            print(person_serializer.errors)

@api_view(['GET'])
def get_all_user_gyms(request, user_id):
    if request.method == 'GET':
        # Query the Send model to get all sends associated with the person
        sends = Send.objects.filter(person=user_id).select_related('boulder__spraywall__gym')
        # Query the Like model to get all sends associated with the person
        likes = Like.objects.filter(person=user_id).select_related('boulder__spraywall__gym')
        # Query the Bookmark model to get all sends associated with the person
        bookmarks = Bookmark.objects.filter(person=user_id).select_related('boulder__spraywall__gym')
        # Query the Circuit model to get all sends associated with the person
        circuits = Circuit.objects.filter(person=user_id).select_related('spraywall__gym')
        # Query the Boulder model to get all set boulders associated with the person
        set_boulders = Boulder.objects.filter(setter_person=user_id).select_related('spraywall__gym')

        # Create a list to store gym information
        gyms = []

        # Create sets to keep track of visited gym IDs and spray wall IDs
        visited_gyms = set()

        # Helper function to check if a gym or spray wall has been visited before
        def is_visited(item_id, visited_set):
            if item_id in visited_set:
                return True
            visited_set.add(item_id)
            return False

        # Loop through the sends to collect unique spray walls for each gym
        for send in sends:
            gym_id = send.boulder.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = send.boulder.spraywall.gym.name
                gym_location = send.boulder.spraywall.gym.location
                gym_type = send.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the liked boulders to collect unique spray walls for each gym
        for like in likes:
            gym_id = like.boulder.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = like.boulder.spraywall.gym.name
                gym_location = like.boulder.spraywall.gym.location
                gym_type = like.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the bookmarked boulders to collect unique spray walls for each gym
        for bookmark in bookmarks:
            gym_id = bookmark.boulder.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = bookmark.boulder.spraywall.gym.name
                gym_location = bookmark.boulder.spraywall.gym.location
                gym_type = bookmark.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the bookmarked boulders to collect unique spray walls for each gym
        for circuit in circuits:
            gym_id = circuit.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = circuit.spraywall.gym.name
                gym_location = circuit.spraywall.gym.location
                gym_type = circuit.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the set boulders to collect unique spray walls for each gym
        for set_boulder in set_boulders:
            gym_id = set_boulder.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = set_boulder.spraywall.gym.name
                gym_location = set_boulder.spraywall.gym.location
                gym_type = set_boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        data = {
            'all_gyms_data': gyms
        }
        return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
def edit_headshot(request, user_id):
    if request.method == 'POST':
        # grab full base64 headshot image
        base64_uri = request.data['url']
        # get user
        user = Person.objects.get(id=user_id)
        # if user already has an existing headshot image, delete url from s3 bucket
        if user.headshot_image_url:
            delete_image_from_s3(user.headshot_image_url)
        # using the raw base64 image data, upload to s3 bucket and retrieve its URL
        url = s3_image_url(base64_uri)
        # grab headshot image width and height
        width = request.data['width']
        height = request.data['height']
        new_headshot_image = {
            'headshot_image_url': url,
            'headshot_image_width': width,
            'headshot_image_height': height,
        }
        # update Person model data with new user headshot URL, width, and height
        person_serializer = PersonSerializer(instance=user, data=new_headshot_image, partial=True)
        if person_serializer.is_valid():
            person_instance = person_serializer.save() # Save the gym instance and get the saved object
            # return headshot image url, width, and height
            headshot_image = {
                'url': person_instance.headshot_image_url,
                'width': person_instance.headshot_image_width,
                'height': person_instance.headshot_image_height,
            }
            data = {
                'headshotImage': headshot_image
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            print(person_serializer.errors)

@api_view(['POST'])
def edit_user_info(request, user_id):
    if request.method == 'POST':
        user = Person.objects.get(id=user_id)
        user_serializer = PersonSerializer(instance=user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_instance = user_serializer.save() # Save the gym instance and get the saved object
            user = {
                'id': user_instance.id,
                'username': user_instance.username,
                'name': user_instance.name,
                'email': user_instance.email,
            }
            data = {
                'user': user
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            print(user_serializer.errors)

@api_view(['PUT'])
def update_user_gym(request, user_id):
    if request.method == 'PUT':
        user = Person.objects.get(id=user_id)
        user_serializer = PersonSerializer(instance=user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
def profile_stats_section(request, user_id, spraywall_id):
    if request.method == 'GET':
        section = request.GET.get('section', '').lower()
        boulders = []
        if section == 'top grade':
            # Get the maximum grade for the user and spraywall_id
            top_grade = Boulder.objects.filter(
                send__person=user_id, spraywall_id=spraywall_id
            ).aggregate(Max('grade'))['grade__max']
            # Get all boulders containing that top grade (could be one or more)
            if top_grade:
                boulders = Boulder.objects.filter(send__person=user_id, spraywall_id=spraywall_id, grade=top_grade).distinct()
        elif section == 'flashes':
            sent_boulders = Boulder.objects.filter(send__person=user_id, spraywall=spraywall_id).distinct()
            for boulder in sent_boulders:
                send_row = Send.objects.filter(boulder=boulder.id).first()
                if send_row.attempts == 1:
                    boulders.append(boulder)
        data = []
        for boulder in boulders:
            data.append(get_boulder_data(boulder, user_id))
        return Response(data, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def profile_boulder_section_list(request, spraywall_id, user_id):
    if request.method == 'GET':
        section = request.GET.get('section', '').lower()
        boulders = []
        boulders_bar_chart_data = None
        # logbook is different to the other sections - different boulder list structure because of sessions and need boulder list bar chart data
        if section == 'logbook':
            # get boulders bar chart data
            boulders_bar_chart_data = get_boulders_bar_chart_data(user_id, spraywall_id)
            # get sent boulders and their send dates
            sent_boulders = get_sent_boulders(user_id, spraywall_id)
            # get list containing each session of boulders - including session number (title), date of session, and data containing those session boulders sent
            boulders = get_session_boulders(sent_boulders, user_id)
        else:
            boulders = get_section_boulders(section, user_id, spraywall_id)
        data = {
            'section': boulders,
            'bouldersBarChartData': boulders_bar_chart_data,
        }
        return Response(data, status=status.HTTP_200_OK)