from .common_imports import *
from django.utils import timezone
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

def paginate_activities(request, activities):
    # Implement your pagination logic here or use an existing Django paginator
    # For example, you can use Django's built-in Paginator class:
    # paginator = Paginator(activities, YOUR_PAGE_SIZE)
    # page_number = request.GET.get('page')
    # paginated_activities = paginator.get_page(page_number)
    # return paginated_activities
    paginator = UserActivityPagination()
    return paginator.paginate_queryset(activities, request)


def format_activity_data(activity):
    formatted_date = DateFormat(activity.date_created).format('F j, Y')
    date_stamp = abbreviate_timesince(timesince(activity.date_created, timezone.now()).split(',')[0])

    return {
        'id': activity.id,
        'action': activity.action,
        'item': activity.item,
        'otherInfo': activity.other_info,
        'spraywallName': activity.spraywall.name,
        'date': formatted_date,
        'dateStamp': date_stamp,
        'rawDate': activity.date_created,
        'username': activity.person.username,
    }