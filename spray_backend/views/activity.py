from spray_backend.utils.activity import *
    
@api_view(['GET'])
def user_activity(request, user_id, gym_id):
    if request.method == 'GET':
        spraywalls = SprayWall.objects.filter(gym=gym_id)

        # Use select_related to fetch related spraywall and person objects
        activities = Activity.objects.filter(person=user_id, spraywall__in=spraywalls).select_related('spraywall', 'person').order_by('-date_created')
        # paginated activities
        paginated_activities = paginate_activities(request, activities)
        # get array of formatted activity data
        activity_data = [
            format_activity_data(activity) for activity in paginated_activities
        ]
        data = {
            'activityData': activity_data
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)