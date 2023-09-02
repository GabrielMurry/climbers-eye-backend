from . import *

@api_view(['GET'])
def profile_quick_data(request, user_id, spraywall_id):
    if request.method == 'GET':
        boulders_section_quick_data = [
            {
                'title': 'Statistics',
                'data': '-'
            },
            {
                'title': 'Logbook',
                'data': 0
            },
            {
                'title': 'Likes',
                'data': 0
            },
            {
                'title': 'Bookmarks',
                'data': 0
            },
            {
                'title': 'Creations',
                'data': 0
            },
        ]
        
        # logbook count (sends)
        boulders = Boulder.objects.filter(spraywall=spraywall_id)
        # get the total count of user's successful climbs
        sends_count = 0
        top_grade = '4a/V0'
        temp = []
        for boulder in boulders:
            send_row = Send.objects.filter(person=user_id, boulder=boulder.id)
            if send_row.exists():
                send_obj = send_row.first()  # Access the first object in the queryset
                # finding top grade (hardest climbed grade difficulty)
                grade_idx = boulder_grades[send_obj.grade]
                top_grade_idx = boulder_grades[top_grade]
                if grade_idx > top_grade_idx:
                    top_grade = send_obj.grade
                sends_count += 1
        boulders_section_quick_data[0]['data'] = top_grade
        boulders_section_quick_data[1]['data'] = sends_count

        # creations count
        boulders = Boulder.objects.filter(spraywall=spraywall_id, setter_person=user_id)
        # established count --> a published boulder with at least 1 send. NOT a project. 
        established_count = 0
        projects_count = 0
        total_sends_count = 0
        for boulder in boulders:
            if boulder.sends_count > 0:
                established_count += 1
            else:
                projects_count += 1
            total_sends_count += boulder.sends_count
        boulders_section_quick_data[4]['data'] = established_count + projects_count

        # likes count
        boulders = Boulder.objects.filter(spraywall=spraywall_id)
        likes_count = 0
        for boulder in boulders:
            liked_row = Like.objects.filter(person=user_id, boulder=boulder.id)
            if liked_row.exists():
                likes_count += 1
        boulders_section_quick_data[2]['data'] = likes_count

        # bookmarks count
        boulders = Boulder.objects.filter(spraywall=spraywall_id)
        bookmarks_count = 0
        for boulder in boulders:
            bookmarked_row = Bookmark.objects.filter(person=user_id, boulder=boulder.id)
            if bookmarked_row.exists():
                bookmarks_count += 1
        boulders_section_quick_data[3]['data'] = bookmarks_count

        data = {
            'bouldersSectionQuickData': boulders_section_quick_data
        }

        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def profile(request, user_id, spraywall_id):
    if request.method == 'GET':
        section = request.GET.get('section', '').lower()
        print(section)
        if section == 'logbook':
            boulders = Boulder.objects.filter(spraywall=spraywall_id)
            # get the total count of user's successful climbs
            sends_count = 0
            flash_count = 0
            top_grade = '4a/V0'
            temp = []
            for boulder in boulders:
                send_row = Send.objects.filter(person=user_id, boulder=boulder.id)
                if send_row.exists():
                    send_obj = send_row.first()  # Access the first object in the queryset
                    # flash_count
                    if send_obj.attempts == 1:
                        flash_count += 1
                    # finding top grade (hardest climbed grade difficulty)
                    grade_idx = boulder_grades[send_obj.grade]
                    top_grade_idx = boulder_grades[top_grade]
                    if grade_idx > top_grade_idx:
                        top_grade = send_obj.grade
                    sends_count += 1
                    temp.append(boulder)
            boulder_data = get_boulder_data(temp, user_id, spraywall_id)
            other_data = {'sendsCount': sends_count, 'flashCount': flash_count, 'topGrade': top_grade}
        elif section == 'creations':
            # boulders in a particular spraywall and created by a particular user
            boulders = Boulder.objects.filter(spraywall=spraywall_id, setter_person=user_id)
            # established count --> a published boulder with at least 1 send. NOT a project. 
            established_count = 0
            projects_count = 0
            total_sends_count = 0
            for boulder in boulders:
                if boulder.sends_count > 0:
                    established_count += 1
                else:
                    projects_count += 1
                total_sends_count += boulder.sends_count
            boulder_data = get_boulder_data(boulders, user_id, spraywall_id)
            other_data = {'establishedCount': established_count, 'projectsCount': projects_count, 'totalSendsCount': total_sends_count}
        elif section == 'likes':
            boulders = Boulder.objects.filter(spraywall=spraywall_id)
            likes_count = 0
            flash_count = 0
            top_grade = '4a/V0'
            temp = []
            for boulder in boulders:
                liked_row = Like.objects.filter(person=user_id, boulder=boulder.id)
                if liked_row.exists():
                    likes_count += 1
                    send_row = Send.objects.filter(person=user_id, boulder=boulder.id)
                    send_obj = send_row.first()  # Access the first object in the queryset
                    # flash_count
                    if send_obj.attempts == 1:
                        flash_count += 1
                    # finding top grade (hardest climbed grade difficulty)
                    grade_idx = boulder_grades[send_obj.grade]
                    top_grade_idx = boulder_grades[top_grade]
                    if grade_idx > top_grade_idx:
                        top_grade = send_obj.grade
                    temp.append(boulder)
            boulder_data = get_boulder_data(temp, user_id, spraywall_id)
            other_data = {'likesCount': likes_count, 'flashCount': flash_count, 'topGrade': top_grade}
        elif section == 'bookmarks':
            boulders = Boulder.objects.filter(spraywall=spraywall_id)
            bookmarks_count = 0
            flash_count = 0
            top_grade = '4a/V0'
            temp = []
            for boulder in boulders:
                bookmarked_row = Bookmark.objects.filter(person=user_id, boulder=boulder.id)
                if bookmarked_row.exists():
                    bookmarks_count += 1
                    send_row = Send.objects.filter(person=user_id, boulder=boulder.id)
                    send_obj = send_row.first()  # Access the first object in the queryset
                    # flash_count
                    if send_obj.attempts == 1:
                        flash_count += 1
                    # finding top grade (hardest climbed grade difficulty)
                    grade_idx = boulder_grades[send_obj.grade]
                    top_grade_idx = boulder_grades[top_grade]
                    if grade_idx > top_grade_idx:
                        top_grade = send_obj.grade
                    temp.append(boulder)
            boulder_data = get_boulder_data(temp, user_id, spraywall_id)
            other_data = {'bookmarksCount': bookmarks_count, 'flashCount': flash_count, 'topGrade': top_grade}
        elif section == 'circuits':
            circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
            circuit_boulders_count = 0
            circuits_data = []
            for circuit in circuits:
                # retrieving all boulder data in particular circuit
                boulders = circuit.boulders.all()
                circuit_boulders_count += len(boulders)
                boulder_data = get_boulder_data(boulders, user_id, spraywall_id)
                # putting boulder data inside circuits data
                circuits_data.append({
                    'id': circuit.id,
                    'name': circuit.name,
                    'description': circuit.description,
                    'color': circuit.color,
                    'private': circuit.private,
                    'boulderData': boulder_data,
                })
            other_data = {'circuitsCount': len(circuits), 'circuitBouldersCount': circuit_boulders_count}
            data = {
                'circuitsData': circuits_data,
                'otherData': other_data,
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        data = {
            'boulderData': boulder_data,
            'otherData': other_data,
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_user_circuits(request, user_id, spraywall_id):
    if request.method == 'GET':
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        circuits_data = []
        for circuit in circuits:
            # retrieving all boulder data in particular circuit
            boulders = circuit.boulders.all()
            boulder_data = get_boulder_data(boulders, user_id, spraywall_id)
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
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def add_profile_banner_image(request, user_id):
    if request.method == 'POST':
        person = Person.objects.get(id=user_id)
        person_serializer = PersonSerializer(instance=person, data=request.data, partial=True)
        if person_serializer.is_valid():
            person_serializer.save()
            return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
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
        visited_spraywalls = set()

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
                gym_location = send.boulder.spraywall.gym.location
                gym_type = send.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the bookmarked boulders to collect unique spray walls for each gym
        for bookmark in bookmarks:
            gym_id = bookmark.boulder.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = bookmark.boulder.spraywall.gym.name
                gym_location = send.boulder.spraywall.gym.location
                gym_type = send.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the bookmarked boulders to collect unique spray walls for each gym
        for circuit in circuits:
            gym_id = circuit.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = circuit.spraywall.gym.name
                gym_location = send.boulder.spraywall.gym.location
                gym_type = send.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)
        # Loop through the set boulders to collect unique spray walls for each gym
        for set_boulder in set_boulders:
            gym_id = set_boulder.spraywall.gym.id
            if not is_visited(gym_id, visited_gyms):
                gym_name = set_boulder.spraywall.gym.name
                gym_location = send.boulder.spraywall.gym.location
                gym_type = send.boulder.spraywall.gym.type
                spraywalls = get_spraywalls(gym_id)
                gym_dict = {'id': gym_id, 'name': gym_name, 'location': gym_location, 'type': gym_type, 'spraywalls': spraywalls}
                gyms.append(gym_dict)

        # # looping through our unique gyms to find used spray walls that correlate with each gym (sends, likes, bookmarks, setter/creation)
        # for gym in gyms:
        #     for send in sends:
        #         gym_id = send.boulder.spraywall.gym.id
        #         if gym_id == gym['id']:
        #             if not is_visited(send.boulder.spraywall.id, visited_spraywalls):
        #                 spraywall_name = send.boulder.spraywall.name
        #                 gym['spraywalls'].append({'id': send.boulder.spraywall.id, 'name': spraywall_name})
        #     for like in likes:
        #         gym_id = like.boulder.spraywall.gym.id
        #         if gym_id == gym['id']:
        #             if not is_visited(like.boulder.spraywall.id, visited_spraywalls):
        #                 spraywall_name = like.boulder.spraywall.name
        #                 gym['spraywalls'].append({'id': like.boulder.spraywall.id, 'name': spraywall_name})
        #     for bookmark in bookmarks:
        #         gym_id = bookmark.boulder.spraywall.gym.id
        #         if gym_id == gym['id']:
        #             if not is_visited(bookmark.boulder.spraywall.id, visited_spraywalls):
        #                 spraywall_name = bookmark.boulder.spraywall.name
        #                 gym['spraywalls'].append({'id': bookmark.boulder.spraywall.id, 'name': spraywall_name})
        #     for circuit in circuits:
        #         gym_id = circuit.spraywall.gym.id
        #         if gym_id == gym['id']:
        #             if not is_visited(circuit.spraywall.id, visited_spraywalls):
        #                 spraywall_name = circuit.spraywall.name
        #                 gym['spraywalls'].append({'id': circuit.spraywall.id, 'name': spraywall_name})
        #     for set_boulder in set_boulders:
        #         gym_id = set_boulder.spraywall.gym.id
        #         if gym_id == gym['id']:
        #             if not is_visited(set_boulder.spraywall.id, visited_spraywalls):
        #                 spraywall_name = set_boulder.spraywall.name
        #                 gym['spraywalls'].append({'id': set_boulder.spraywall.id, 'name': spraywall_name})

        # Now you have a list "gyms_with_spraywalls" containing gym information and their associated unique spray walls
        data = {
            'all_gyms_data': gyms
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def profile_main(request, user_id):
    if request.method == 'GET':
        # Retrieve the 'walls' query parameter as a comma-separated string
        spraywall_id_str = request.GET.get('walls', '')

        # Split the string into a list of individual strings (IDs)
        spraywall_id_arr = spraywall_id_str.split(',')

        # Convert each element from string to integer using list comprehension
        spraywall_id_arr = [int(wall) for wall in spraywall_id_arr]
        
        # Initialize a list to store the final output
        output_list = []
        
        for spraywall_id in spraywall_id_arr:
            try:
                spraywall_row = SprayWall.objects.get(id=spraywall_id)
                gym_row = spraywall_row.gym  # Assuming SprayWall has a ForeignKey to Gym model
                
                # Create a dictionary for the spraywall details
                spraywall_dict = {
                    'spraywallID': spraywall_row.id,
                    'spraywallName': spraywall_row.name,
                    'url': spraywall_row.spraywall_image_url,
                }

                # Create a dictionary for the gym details
                gym_dict = {
                    'gymID': gym_row.id,
                    'gymName': gym_row.name,
                    'spraywalls': [spraywall_dict],
                }

                # Check if the gym is already in the output_list
                # If it is, append the spraywall to its existing 'spraywalls' list
                # If not, add the gym dictionary to the output_list
                index = next((i for i, item in enumerate(output_list) if item['gymID'] == gym_row.id), None)
                if index is not None:
                    output_list[index]['spraywalls'].append(spraywall_dict)
                else:
                    output_list.append(gym_dict)
            
            except SprayWall.DoesNotExist:
                # Handle the case when a spraywall with the given ID does not exist
                pass

        data = {
            'gym_data': output_list
        }

        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

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
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
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
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(user_serializer.errors)

@api_view(['PUT'])
def update_user_gym(request, user_id):
    if request.method == 'PUT':
        user = Person.objects.get(id=user_id)
        user_serializer = PersonSerializer(instance=user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)

# @api_view(['PUT'])
# def update_user_gym(request, user_id):
#     try:
#         user = Person.objects.get(id=user_id)
#     except Person.DoesNotExist:
#         raise Http404("User not found")

#     if request.method == 'PUT':
#         user_serializer = PersonSerializer(instance=user, data=request.data, partial=True)
#         if user_serializer.is_valid():
#             user_serializer.save()
#             return Response({'message': 'User gym ID updated successfully'}, status=status.HTTP_200_OK)
#         return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)