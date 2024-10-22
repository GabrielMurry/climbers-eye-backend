from django_filters import rest_framework as filters
from django.db.models import Q
from api.boulder.models import Boulder
from api.gym.models import Gym

class BoulderFilter(filters.FilterSet):
    search = filters.CharFilter(field_name='name', lookup_expr='icontains')
    grade = filters.RangeFilter(method='grade_method')
    activity = filters.CharFilter(method='activity_method')
    status = filters.CharFilter(method='status_method')
    circuit = filters.CharFilter(method='circuit_method')
    sort = filters.CharFilter(method='sort_method')
    exclude_ids = filters.CharFilter(method='exclude_ids_method')

    class Meta:
        model = Boulder
        fields = []
    
    def grade_method(self, queryset, name, value):
        # Extract the min and max values from the range
        min_grade = value.start
        max_grade = value.stop
        # Filter queryset from range of boulder grades given (inclusive) - includes all non-graded (project) boulders placed after the graded (established) boulders.
        queryset = queryset.filter(Q(grade__gte=min_grade, grade__lte=max_grade) | Q(grade=None))
        return queryset
    
    def activity_method(self, queryset, name, value):
        match value:
            case 'liked':
                queryset = queryset.filter(is_liked=True)
            case 'bookmarked':
                queryset = queryset.filter(is_bookmarked=True)
            case 'sent':
                queryset = queryset.filter(is_sent=True)
        return queryset
    
    def status_method(self, queryset, name, value):
        match value:
            case 'all':
                pass
            case 'established':
                queryset = queryset.filter(grade__isnull=False)
            case 'projects':
                queryset = queryset.filter(grade__isnull=True)
            case 'drafts':
                queryset = queryset.filter(setter=self.request.user.id, publish=False)
        return queryset
    
    def circuit_method(self, queryset, name, value):
        circuit_id = value
        if circuit_id == 'null':
            return queryset
        else:
            return queryset.filter(circuits__id=circuit_id)
            

    def sort_method(self, queryset, name, value):
        match value:
            case 'grade': # order by grade (least difficult to greatest difficult)
                queryset = queryset.order_by('grade')
            case 'popular': # order by num of sends (greatest to least)
                queryset = queryset.order_by('-sends_count')
            case 'newest': # order by date created (newest to oldest)
                queryset = queryset.order_by('-date_created')
        return queryset
    
    def exclude_ids_method(self, queryset, name, value):
        # Exclude the IDs passed as a comma-separated string
        exclude_ids = value.split(',')
        return queryset.exclude(id__in=exclude_ids)
    
class GymFilter(filters.FilterSet):
    search = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Gym
        fields = []