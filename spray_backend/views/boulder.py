from . import *

@api_view(['POST'])    
def composite(request):
    drawing_image, photo_image = base64_string_to_image(request.data.get('drawing'), request.data.get('photo'))
    drawing_image = increase_drawing_opacity(drawing_image)
    drawing_image = mask_drawing(drawing_image, photo_image)
    result = combine_images(drawing_image, photo_image)
    result_uri = 'data:image/png;base64,' + image_to_base64_string(result)
    data = {
        'uri': result_uri
    }
    return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def add_boulder(request, spraywall_id, user_id):
    if request.method == 'POST':
        boulder = request.data
        image_url = s3_image_url(boulder['image_data'])
        boulder_data = {
            'name': boulder['name'],
            'description': boulder['description'],
            'matching': boulder['matching'],
            'publish': boulder['publish'],
            'boulder_image_url': image_url,
            'boulder_image_width': boulder['image_width'],
            'boulder_image_height': boulder['image_height'],
            'spraywall': spraywall_id,
            'setter_person': user_id,
        }
        # using the boulder data, we create a brand new Boulder row in Boulder table
        boulder_serializer = BoulderSerializer(data=boulder_data)
        if boulder_serializer.is_valid():
            boulder_instance = boulder_serializer.save()
            boulder = Boulder.objects.get(id=boulder_instance.id)
            data = {
                'name': boulder.name, 
                'description': boulder.description, 
                'matching': boulder.matching, 
                'publish': boulder.publish,
                'url': boulder.boulder_image_url,
                'width': boulder.boulder_image_width,
                'height': boulder.boulder_image_height,
                'setter': boulder.setter_person.username,
                'firstAscent': boulder.first_ascent_person.username if boulder.first_ascent_person else None,
                'sends': boulder.sends_count,
                'grade': boulder.grade,
                'quality': boulder.quality,
                'likes': boulder.likes_count,
                'id': boulder.id
            }
            add_activity('boulder', boulder.id, 'created', boulder.name, None, spraywall_id, user_id)
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(boulder_serializer.errors)

@api_view(['GET'])
def list(request, spraywall_id, user_id):
    if request.method == 'GET':
        # get filter queries from attached to endpoint request
        search_query, sort_by, min_grade_index, max_grade_index, circuits, climb_type, filter_status = get_filter_queries(request)
        # get all boulders on the specified spraywall
        boulders = Boulder.objects.filter(spraywall=spraywall_id)
        # Filter
        boulders = filter_by_search_query(boulders, search_query)
        boulders = filter_by_circuits(boulders, circuits)
        boulders = filter_by_sort_by(boulders, sort_by, user_id)
        boulders = filter_by_status(boulders, filter_status, user_id)
        boulders = filter_by_grades(boulders, min_grade_index, max_grade_index)
        # get everything except image data, image width, image height --> image data takes very long to load especially when grabbing every single boulder
        data = get_boulder_data(boulders, user_id, spraywall_id)
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def logbook_list(request, spraywall_id, user_id):
    if request.method == 'GET':
        # get filter queries from attached to endpoint request
        section = request.GET.get('section', '').lower()
        search_query, sort_by, min_grade_index, max_grade_index, circuits, climb_type, filter_status = get_filter_queries(request)
        # get all logged boulders (sent boulders) on the specified spraywall
        boulders = []
        if section == 'logbook':
            boulders = Boulder.objects.filter(send__person=user_id, spraywall_id=spraywall_id)
        elif section == 'likes':
            boulders = Boulder.objects.filter(like__person=user_id, spraywall_id=spraywall_id)
        elif section == 'bookmarks':
            boulders = Boulder.objects.filter(bookmark__person=user_id, spraywall_id=spraywall_id)
        elif section == 'creations':
            boulders = Boulder.objects.filter(setter_person=user_id, spraywall_id=spraywall_id)
        # Filter
        boulders = filter_by_search_query(boulders, search_query)
        boulders = filter_by_circuits(boulders, circuits)
        boulders = filter_by_sort_by(boulders, sort_by, user_id)
        boulders = filter_by_status(boulders, filter_status, user_id)
        boulders = filter_by_grades(boulders, min_grade_index, max_grade_index)
        # get everything except image data, image width, image height --> image data takes very long to load especially when grabbing every single boulder
        data = get_boulder_data(boulders, user_id, spraywall_id)
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST', 'DELETE'])
def like_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        data = { 'person': user_id, 'boulder': boulder_id }
        like_serializer = LikeSerializer(data=data)
        if like_serializer.is_valid():
            like_instance = like_serializer.save()
            data = {
                'isLiked': True
            }
            add_activity('like', like_instance.id, 'liked', like_instance.boulder.name, like_instance.boulder.grade, like_instance.boulder.spraywall.id, user_id)
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(like_serializer.errors)
    if request.method == 'DELETE':
        liked_row = Like.objects.filter(person=user_id, boulder=boulder_id)
        liked_row.delete()
        data = {
            'isLiked': False
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST', 'DELETE'])
def bookmark_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        data = { 'person': user_id, 'boulder': boulder_id }
        bookmark_serializer = BookmarkSerializer(data=data)
        if bookmark_serializer.is_valid():
            bookmark_instance = bookmark_serializer.save()
            data = {
                'isBookmarked': True
            }
            add_activity('bookmark', bookmark_instance.id, 'bookmarked', bookmark_instance.boulder.name, bookmark_instance.boulder.grade, bookmark_instance.boulder.spraywall.id, user_id)
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(bookmark_serializer.errors)
    if request.method == 'DELETE':
        bookmark_row = Bookmark.objects.filter(person=user_id, boulder=boulder_id)
        bookmark_row.delete()
        data = {
            'isBookmarked': False
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def sent_boulder(request, boulder_id):
    if request.method == 'POST':
        # post new row that details user's attempts, chosen difficulty, quality, and notes for a particular boulder
        # update new info for the actual Boulder --> ?
        send_serializer = SendSerializer(data=request.data)
        if send_serializer.is_valid():
            send_instance = send_serializer.save()
            boulder = Boulder.objects.get(id=boulder_id)
            boulder.sends_count += 1
            boulder.grade = request.data.get('grade')
            boulder.quality = request.data.get('quality')
            if boulder.first_ascent_person is None:
                person = Person.objects.get(id=request.data.get('person'))
                boulder.first_ascent_person = person
            boulder.save()
            add_activity('send', send_instance.id, 'sent', send_instance.boulder.name, send_instance.grade, send_instance.boulder.spraywall.id, send_instance.person.id)
            return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
        else:
            print(send_serializer.errors)

@api_view(['GET'])
def updated_boulder_data(request, boulder_id, user_id):
    if request.method == 'GET':
        # get the updated data for the boulder on the Boulder Screen
        boulder = Boulder.objects.get(id=boulder_id)
        # check if user sent the boulder
        sent_row = Send.objects.filter(person=user_id, boulder=boulder_id)
        sent_boulder = False
        if sent_row.exists():
            sent_boulder = True
        # check if user liked the boulder
        liked_row = Like.objects.filter(person=user_id, boulder=boulder_id)
        liked_boulder = False
        if liked_row.exists():
            liked_boulder = True
        # check if user bookmarked the boulder
        bookmarked_row = Bookmark.objects.filter(person=user_id, boulder=boulder_id)
        bookmarked_boulder = False
        if bookmarked_row.exists():
            bookmarked_boulder = True
        # check if boulder is in a circuit
        circuit = Circuit.objects.filter(person=user_id, boulders=boulder_id)
        inCircuit = False
        if circuit.exists():
            inCircuit = True
        data = {
            'grade': boulder.grade,
            'quality': boulder.quality,
            'firstAscent': boulder.first_ascent_person.username if boulder.first_ascent_person else None, 
            'isSent': sent_boulder,
            'isLiked': liked_boulder,
            'isBookmarked': bookmarked_boulder,
            'inCircuit': inCircuit
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['DELETE'])
def delete_boulder(request, boulder_id):
    if request.method == 'DELETE':
        boulder_row = Boulder.objects.get(id=boulder_id)
        # delete boulder image from amazon s3
        delete_image_from_s3(boulder_row.boulder_image_url)
        boulder_row.delete()
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
    
@api_view(['POST', 'DELETE'])
def add_or_remove_boulder_in_circuit(request, circuit_id, boulder_id):
    # get particular circuit and boulder instance
    circuit = Circuit.objects.get(pk=circuit_id)
    boulder = Boulder.objects.get(pk=boulder_id)
    if request.method == 'POST':
        # add new boulder to circuit's boulder list
        circuit.boulders.add(boulder)
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
    if request.method == 'DELETE':
        # remove particular boulder from circuit's boulder list
        circuit.boulders.remove(boulder)
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def get_boulders_from_circuit(request, user_id, circuit_id):
    if request.method == 'GET':
        # Retrieving boulders for a circuit
        circuit = Circuit.objects.get(pk=circuit_id)
        boulders = circuit.boulders.all()
        data = []
        for boulder in boulders:
            liked_row = Like.objects.filter(person=user_id, boulder=boulder.id)
            liked_boulder = False
            if liked_row.exists():
                liked_boulder = True
            bookmarked_row = Bookmark.objects.filter(person=user_id, boulder=boulder.id)
            bookmarked_boulder = False
            if bookmarked_row.exists():
                bookmarked_boulder = True
            sent_row = Send.objects.filter(person=user_id, boulder=boulder.id)
            sent_boulder = False
            if sent_row.exists():
                sent_boulder = True
            data.append({
                'id': boulder.id, 
                'name': boulder.name, 
                'description': boulder.description, 
                'matching': boulder.matching, 
                'publish': boulder.publish, 
                'setter': boulder.setter_person.username, 
                'firstAscent': boulder.first_ascent_person.username if boulder.first_ascent_person else None, 
                'sends': boulder.sends_count, 
                'grade': boulder.grade, 
                'quality': boulder.quality, 
                'likes': boulder.likes_count,
                'isLiked': liked_boulder,
                'isBookmarked': bookmarked_boulder,
                'isSent': sent_boulder
            })
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def boulder_stats(request, boulder_id):
    if request.method == 'GET':
        # get all people who have sent the boulder
        # get each person's suggested grade
        # get the name of boulder, setter of boulder, first ascenter, and number of sends
        grade_counts = (
            Send.objects
            .filter(boulder=boulder_id)
            .values('grade')
            .annotate(count=Count('grade'))
            .order_by('grade')
        )
        is_project = True
        for item in grade_counts:
            for boulder in boulders_bar_chart_data:
                if boulder['x'] == item['grade']:
                    boulder['y'] = item['count']
                    is_project = False
                    break
        # result = [{'grade': item['grade'], 'count': item['count']} for item in grade_counts]
        boulders_pie_chart_data = None
        if not is_project:
            totalGradersPie = sum(boulder['y'] for boulder in boulders_bar_chart_data)
            bouldersWithPercentagePie = [
                {**boulder, 'percentage': (boulder['y'] / totalGradersPie) * 100}
                for boulder in boulders_bar_chart_data if boulder['y'] > 0
            ]
            boulders_pie_chart_data = sorted(bouldersWithPercentagePie, key=lambda x: x['percentage'], reverse=True)
            # for pie data, I need to change properties 'x' to 'label' and 'y' to 'value', keep percentage
            boulders_pie_chart_data = [{'label': obj['x'], 'value': obj['y'], 'percentage': obj['percentage'], 'color': colors[idx]} for idx, obj in enumerate(boulders_pie_chart_data)]
            print(boulders_pie_chart_data)
        data = {
            'bouldersBarChartData': boulders_bar_chart_data,
            'bouldersPieChartData': boulders_pie_chart_data,
            'isProject': is_project
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)