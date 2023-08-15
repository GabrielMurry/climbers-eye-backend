from . import *
from django.utils import timezone
from django.utils.dateformat import DateFormat
from django.utils.timesince import timesince
from rest_framework.pagination import PageNumberPagination

def abbreviate_timesince(timesince_str):
    time_units = ['year', 'week', 'day', 'hour', 'minute', 'second']
    abbreviations = ['y', 'w', 'd', 'h', 'm', 's']
    
    for idx, unit in enumerate(time_units):
        if unit in timesince_str:
            value = timesince_str.split()[0]
            return value + abbreviations[idx]
    
    return timesince_str.strip()

class UserActivityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# @api_view(['GET'])
# def user_activity(request, user_id, gym_id):
#     if request.method == 'GET':
#         activity_data = []
#         spraywalls = SprayWall.objects.filter(gym=gym_id)
#         for spraywall in spraywalls:
#             # get all user's activities in each spray wall
#             activities = Activity.objects.filter(person=user_id, spraywall=spraywall.id)
#             for activity in activities:
#                 formatted_date = DateFormat(activity.date_created).format('F j, Y')
#                 date_stamp = abbreviate_timesince(timesince(activity.date_created, timezone.now()).split(',')[0])
#                 activity_data.append({
#                     'id': activity.id,
#                     'action': activity.action,
#                     'message': activity.message,
#                     'spraywallName': spraywall.name,
#                     'date': formatted_date,
#                     'dateStamp': date_stamp,
#                     'rawDate': activity.date_created,  # Store the raw datetime for sorting
#                 })
        
#         # Sort the sent_data array based on the raw datetime
#         sorted_activity_data = sorted(activity_data, key=lambda x: x['rawDate'], reverse=True)
        
#         data = {
#             'activityData': sorted_activity_data
#         }
#         return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def user_activity(request, user_id, gym_id):
    if request.method == 'GET':
        spraywalls = SprayWall.objects.filter(gym=gym_id)
        activities = Activity.objects.filter(person=user_id, spraywall__in=spraywalls).order_by('-date_created')

        paginator = UserActivityPagination()
        paginated_activities = paginator.paginate_queryset(activities, request)

        activity_data = []
        for activity in paginated_activities:
            print(activity)
            formatted_date = DateFormat(activity.date_created).format('F j, Y')
            date_stamp = abbreviate_timesince(timesince(activity.date_created, timezone.now()).split(',')[0])
            activity_data.append({
                'id': activity.id,
                'action': activity.action,
                'item': activity.item,
                'otherInfo': activity.other_info,
                'spraywallName': activity.spraywall.name,
                'date': formatted_date,
                'dateStamp': date_stamp,
                'rawDate': activity.date_created,
                'username': activity.person.username,
            })

        data = {
            'activityData': activity_data
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)