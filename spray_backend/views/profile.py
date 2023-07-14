from . import *

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