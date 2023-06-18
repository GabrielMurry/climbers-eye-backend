from ..models import Gym, SprayWall, Person, Boulder, Like, Send, Circuit, Bookmark
from utils.constants import boulder_grades
from django.db.models import Q
import json

def get_filter_queries(request):
    # Convert search query to lowercase
    search_query = request.GET.get('search', '').lower()
    sort_by = request.GET.get('sortBy', '').lower()
    min_grade_index = int(request.GET.get('minGradeIndex', '').lower())
    max_grade_index = int(request.GET.get('maxGradeIndex', '').lower())
    circuits = request.GET.get('circuits', '').lower()
    circuits = json.loads(circuits)
    climb_type = request.GET.get('climbType', '').lower()
    # can't be named 'status' because our Response object already has property 'status'
    filter_status = request.GET.get('status', '').lower()
    return search_query, sort_by, min_grade_index, max_grade_index, circuits, climb_type, filter_status

def filter_by_search_query(boulders, search_query):
    if len(search_query) > 0:
        # query boulders based on whatever matches name, grade, or setter username
        boulders = boulders.filter(Q(name__icontains=search_query) | Q(grade__icontains=search_query) | Q(setter_person__username__icontains=search_query))
    return boulders

def filter_by_circuits(boulders, circuits):
    # if we are filtering by circuits, find all boulders in that circuit (circuit should only be available in the current spraywall so no need to specify which spraywall)
    if circuits != []:
        for circuit in circuits:
            boulders = boulders.filter(circuits__id__in=circuits).distinct() # distinct because if you want all boulders in multiple circuits, there could be duplicates of boulders. Want all distinct boulders no duplicates
    return boulders
    
def filter_by_sort_by(boulders, sort_by, user_id):
    if sort_by == 'popular':
            return boulders.order_by('-sends_count')
    elif sort_by == 'liked':
        temp = []
        for boulder in boulders:
            liked_row = Like.objects.filter(person=user_id, boulder=boulder.id)
            if liked_row.exists():
                temp.append(boulder)
        return temp
    elif sort_by == 'bookmarked':
        temp = []
        for boulder in boulders:
            bookmarked_row = Bookmark.objects.filter(person=user_id, boulder=boulder.id)
            if bookmarked_row.exists():
                temp.append(boulder)
        return temp
    elif sort_by == 'recent':
        return boulders.order_by('-date_created')
    
def filter_by_status(boulders, status, user_id):
     # Filtering by status. 'all' is default and applies to all types of status - so no condition for 'all'
    if status == 'all':
          return boulders
    elif status == 'established':
        temp = []
        for boulder in boulders:
            sent_row = Send.objects.filter(person=user_id, boulder=boulder.id)
            if sent_row.exists():
                temp.append(boulder)
        return temp
    elif status == 'projects':
        temp = []
        for boulder in boulders:
            sent_row = Send.objects.filter(person=user_id, boulder=boulder.id)
            if not sent_row.exists():
                temp.append(boulder)
        return temp
    
def filter_by_grades(boulders, min_grade_index, max_grade_index):
     # filter through grades (include status labeled 'project' (graded 'None'))
    new_boulders = []
    for boulder in boulders:
        # if boulder is not a project (still include projects but calculating grade's index requires non null type)
        if boulder.grade is not None:
            grade_idx = boulder_grades[boulder.grade]
            if grade_idx >= min_grade_index and grade_idx <= max_grade_index:
                new_boulders.append(boulder)
        else:
            new_boulders.append(boulder)
    return new_boulders

# IMPROVE
def get_boulder_data(boulders, user_id, spraywall_id):
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
        # if particular boulder is in at least one of user's circuit in this particular spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        in_circuit = False
        for circuit in circuits:
            boulder_is_in_circuit = circuit.boulders.filter(pk=boulder.id)
            if boulder_is_in_circuit.exists():
                in_circuit = True
                break
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
            'isSent': sent_boulder,
            'inCircuit': in_circuit
        })
    return data