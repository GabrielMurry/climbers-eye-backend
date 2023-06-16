from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .forms import CreateUserForm
from .models import Gym, SprayWall, Person, Boulder, Like, Send, Circuit, Bookmark
from spray_backend.models import Movie
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import GymSerializer, SprayWallSerializer, BoulderSerializer, PersonSerializer, LikeSerializer, SendSerializer, CircuitSerializer, BookmarkSerializer
from .helperFunctions.composite import base64_string_to_image, increase_drawing_opacity, mask_drawing, combine_images, image_to_base64_string
from django.middleware.csrf import get_token
from django.db.models import Q, Count
from utils.constants import boulders_bar_chart_data, colors

def movie(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    if movie is not None:
        return render(request, 'movies/movie.html', {'movie': movie})
    else:
        raise Http404('Movie does not exist')
    
@api_view(['GET'])
def csrf_token_view(request):
    if request.method == 'GET':
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token})
    
@api_view(['POST'])
def signup_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.data)
        if form.is_valid():
            form.save()
            person_serializer = PersonSerializer(data=request.data)
            if person_serializer.is_valid():
                person_instance = person_serializer.save()
                csrf_token = get_token(request)
                username = request.data.get('username')
                return Response({'csrfToken': csrf_token, 'userID': person_instance.id, 'username': username}, status=status.HTTP_200_OK)
            else:
                print(person_serializer.errors)
        else:
            print(form.errors)

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            csrf_token = get_token(request)
            person = Person.objects.get(username=username)
            data = {}
            if person.gym_id and person.spraywall.id:
                image_uri = 'data:image/png;base64,' + person.spraywall.spraywall_image_data
                image_width = person.spraywall.spraywall_image_width
                image_height = person.spraywall.spraywall_image_height
                data = {'userID': person.id, 'gymID': person.gym_id, 'gymName': person.gym.name, 'spraywallName': person.spraywall.name, 'spraywallID': person.spraywall.id, 'imageUri': image_uri, 'imageWidth': image_width, 'imageHeight': image_height}
            else:
                data = {'userID': person.id}
            return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        else:
            return Response('Username or password is incorrect')

@api_view(['GET'])
def logout_user(request):
    logout(request)
    return Response('logged out')
    
@api_view(['POST'])    
def composite(request):
    drawing_image, photo_image = base64_string_to_image(request.data.get('drawing'), request.data.get('photo'))
    drawing_image = increase_drawing_opacity(drawing_image)
    drawing_image = mask_drawing(drawing_image, photo_image)
    result = combine_images(drawing_image, photo_image)
    data_uri = 'data:image/png;base64,' + image_to_base64_string(result)
    return Response(data_uri)

@api_view(['POST'])
def add_gym(request, user_id):
    if request.method == 'POST':
        # Add Gym
        gym_serializer = GymSerializer(data=request.data.get('gym'))
        if gym_serializer.is_valid():
            gym_instance = gym_serializer.save() # Save the gym instance and get the saved object
            gym_id = gym_instance.id  # Access the ID of the recently created gym
            request.data['spraywall']['gym'] = gym_id # Insert recently created gym_id as a reference for spraywall's gym foreign key
            # Add Spray Wall
            spraywall_serializer = SprayWallSerializer(data=request.data.get('spraywall'))
            if spraywall_serializer.is_valid():
                spraywall_instance = spraywall_serializer.save()
                spraywall_id = spraywall_instance.id
                # Update Person data: person's gym_id foreign key and spraywall_id foreign key --> signifies person's default Gym and Wall
                person = Person.objects.get(id=user_id)
                person_data = {
                    'gym': gym_id,
                    'spraywall': spraywall_id
                }
                person_serializer = PersonSerializer(instance=person, data=person_data, partial=True) # partial=True allows for partial updates
                if person_serializer.is_valid():
                    person_serializer.save()
                    csrf_token = get_token(request)
                    return Response({'csrfToken': csrf_token}, status=status.HTTP_200_OK)
                else:
                    print(person_serializer.errors)
            else:
                print(spraywall_serializer.errors)
        else:
            print(gym_serializer.errors)

@api_view(['GET'])
def home(request, user_id):
    if request.method == 'GET':
        person = Person.objects.get(id=user_id)
        gym_name = person.gym.name
        spraywall_name = person.spraywall.name
        spraywall_id = person.spraywall.id
        image_uri = 'data:image/png;base64,' + person.spraywall.spraywall_image_data
        image_width = person.spraywall.spraywall_image_width
        image_height = person.spraywall.spraywall_image_height
        data = { 'gymName': gym_name, 'spraywallName': spraywall_name, 'spraywallID': spraywall_id, 'imageUri': image_uri, 'imageWidth': image_width, 'imageHeight': image_height }
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        
@api_view(['GET', 'POST'])
def spraywall(request):
    if request.method == 'POST':
        serializer = SprayWallSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # pass data back in response
            return Response('hi')
    if request.method == 'GET':
        queryset = SprayWall.objects.filter(id=2)
        serializer = SprayWallSerializer(queryset, many=True)
        return Response(serializer.data)

@api_view(['POST'])
def add_boulder(request, user_id):
    if request.method == 'POST':
        person = Person.objects.get(id=user_id)
        request.data['spraywall'] = person.spraywall.id
        request.data['setter_person'] = person.id
        serializer = BoulderSerializer(data=request.data)
        if serializer.is_valid():
            boulder_instance = serializer.save()
            boulder = Boulder.objects.get(id=boulder_instance.id)
            data = {
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
                'id': boulder.id
            }
            csrf_token = get_token(request)
            return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        
@api_view(['GET', 'POST'])
def list(request, spraywall_id, user_id):
    if request.method == 'GET':
        # get all boulders on the specified spraywall
        boulders = Boulder.objects.filter(spraywall=spraywall_id)
        # get everything except image data, image width, image height --> image data takes very long to load especially when grabbing every single boulder
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
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def query_list(request, spraywall_id, user_id):
    if request.method == 'GET':
        # Convert search query to lowercase
        search_query = request.GET.get('search', '').lower()
        # query boulders based on whatever matches name, grade, or setter username
        boulders = Boulder.objects.filter(Q(name__icontains=search_query) | Q(grade__icontains=search_query) | Q(setter_person__username__icontains=search_query), spraywall=spraywall_id)
         # get everything except image data, image width, image height --> image data takes very long to load especially when grabbing every single boulder
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
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)

# @api_view(['GET'])
# def filter_list(request, spraywall_id, user_id):

    
@api_view(['GET'])
def boulder_image(request, boulder_id):
    if request.method == 'GET':
        boulder = Boulder.objects.get(pk=boulder_id)
        data = { 
            'image_uri': "data:image/png;base64," + boulder.boulder_image_data,
            'image_width': boulder.boulder_image_width,
            'image_height': boulder.boulder_image_height,
        }
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)

@api_view(['POST', 'DELETE'])
def like_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        data = { 'person': user_id, 'boulder': boulder_id }
        like_serializer = LikeSerializer(data=data)
        if like_serializer.is_valid():
            like_serializer.save()
            data = {'isLiked': True}
            csrf_token = get_token(request)
            return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        else:
            print(like_serializer.errors)
    if request.method == 'DELETE':
        liked_row = Like.objects.filter(person=user_id, boulder=boulder_id)
        liked_row.delete()
        data = {'isLiked': False}
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST', 'DELETE'])
def bookmark_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        data = { 'person': user_id, 'boulder': boulder_id }
        bookmark_serializer = BookmarkSerializer(data=data)
        if bookmark_serializer.is_valid():
            bookmark_serializer.save()
            data = {'isBookmarked': True}
            csrf_token = get_token(request)
            return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        else:
            print(bookmark_serializer.errors)
    if request.method == 'DELETE':
        bookmark_row = Bookmark.objects.filter(person=user_id, boulder=boulder_id)
        bookmark_row.delete()
        data = {'isBookmarked': False}
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['GET', 'POST'])
def sent_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        # post new row that details user's attempts, chosen difficulty, quality, and notes for a particular boulder
        # update new info for the actual Boulder --> ?
        send_serializer = SendSerializer(data=request.data)
        if send_serializer.is_valid():
            send_serializer.save()
            # sends = Send.objects.filter(boulder=boulder_id)
            # for send in sends:
            boulder = Boulder.objects.get(id=boulder_id)
            boulder.sends_count += 1
            boulder.grade = request.data.get('grade')
            boulder.quality = request.data.get('quality')
            if boulder.first_ascent_person is None:
                person = Person.objects.get(id=request.data.get('person'))
                boulder.first_ascent_person = person
            boulder.save()
            csrf_token = get_token(request)
            return Response({'csrfToken': csrf_token}, status=status.HTTP_200_OK)
        else:
            print(send_serializer.errors)
    if request.method == 'GET':
        # get the updated data for the boulder on the Boulder Screen
        boulder = Boulder.objects.get(id=boulder_id)
        sent_row = Send.objects.filter(person=user_id, boulder=boulder_id)
        sent_boulder = False
        if sent_row.exists():
            sent_boulder = True
        data = {
            'grade': boulder.grade,
            'quality': boulder.quality,
            'firstAscent': boulder.first_ascent_person.username if boulder.first_ascent_person else None, 
            'isSent': sent_boulder
        }
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['DELETE'])
def delete_boulder(request, boulder_id):
    if request.method == 'DELETE':
        boulder_row = Boulder.objects.get(id=boulder_id)
        boulder_row.delete()
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def query_gyms(request):
    if request.method == 'GET':
        # Convert search query to lowercase
        search_query = request.GET.get('search', '').lower()
        gyms = Gym.objects.filter(Q(name__icontains=search_query) | Q(location__icontains=search_query))
         # get everything except image data, image width, image height --> image data takes very long to load especially when grabbing every single boulder
        data = []
        for gym in gyms:
            data.append({
                'id': gym.id, 
                'name': gym.name, 
                'location': gym.location,
            })
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def queried_gym_spraywall(request, gym_id):
    if request.method == 'GET':
        # get gym's spraywall image, width, and height to display on bottom sheet in map screen when user clicks on gym card
        spraywall = SprayWall.objects.get(gym=gym_id)
        data = {
            'imageUri': "data:image/png;base64," + spraywall.spraywall_image_data,
            'imageWidth': spraywall.spraywall_image_width,
            'imageHeight': spraywall.spraywall_image_height,
        }
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['PUT'])
def choose_gym(request, user_id, gym_id):
    if request.method == 'PUT':
        # updating person's default gym and spraywall id to user's chosen gym
        spraywall = SprayWall.objects.get(gym=gym_id)
        person_data = {
            'id': user_id,
            'gym': gym_id,
            'spraywall': spraywall.id
        }
        person = Person.objects.get(id=user_id)
        # update or add user's new default gym and spraywall
        person_serializer = PersonSerializer(instance=person, data=person_data, partial=True)
        if person_serializer.is_valid():
            person_instance = person_serializer.save()
            person_updated = Person.objects.get(id=person_instance.id)
            data = {
                'gymName': person_updated.gym.name,
                'spraywallName': person_updated.spraywall.name,
                'spraywallID': person_updated.spraywall.id,
                'imageUri': "data:image/png;base64," + person_updated.spraywall.spraywall_image_data,
                'imageWidth': person_updated.spraywall.spraywall_image_width,
                'imageHeight': person_updated.spraywall.spraywall_image_height,
            }
            csrf_token = get_token(request)
            return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        else:
            print(person_serializer.errors)

@api_view(['GET'])
def profile(request, user_id):
    if request.method == 'GET':
        # get the total count of user's successful climbs
        sends_count = Send.objects.filter(person=user_id).count()
        # get the total count of user's created boulders
        user_created_boulders_count = Boulder.objects.filter(setter_person=user_id).count()
        # get the total count of user's 'liked' boulders
        likes_count = Like.objects.filter(person=user_id).count()
        data = {
            'sends': sends_count,
            'userCreatedBoulders': user_created_boulders_count,
            'likes': likes_count
        }
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def circuits(request, user_id, spraywall_id, boulder_id):
    if request.method == 'GET':
        # get all circuits associated to that particular user and spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        data = []
        for circuit in circuits:
            boulder_is_in_circuit = circuit.boulders.filter(pk=boulder_id).exists()
            data.append({
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private,
                'isSelected': boulder_is_in_circuit
            })
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    if request.method == 'POST':
        # adding a new circuit (brand new circuits don't initially contain any boulders)
        circuit_serializer = CircuitSerializer(data=request.data, partial=True)
        if circuit_serializer.is_valid():
            circuit = circuit_serializer.save()
            data = {
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private
            }
            csrf_token = get_token(request)
            return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
        else:
            print(circuit_serializer.errors)

@api_view(['DELETE'])
def delete_circuit(request, user_id, spraywall_id, circuit_id):
    if request.method == 'DELETE':
        # deleting a user's particular circuit in a particular spraywall
        circuit_row = Circuit.objects.get(id=circuit_id, person=user_id, spraywall=spraywall_id)
        circuit_row.delete()
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token}, status=status.HTTP_200_OK)
    
@api_view(['POST', 'DELETE'])
def add_or_remove_boulder_in_circuit(request, circuit_id, boulder_id):
    # get particular circuit and boulder instance
    circuit = Circuit.objects.get(pk=circuit_id)
    boulder = Boulder.objects.get(pk=boulder_id)
    if request.method == 'POST':
        # add new boulder to circuit's boulder list
        circuit.boulders.add(boulder)
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token}, status=status.HTTP_200_OK)
    if request.method == 'DELETE':
        # remove particular boulder from circuit's boulder list
        circuit.boulders.remove(boulder)
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token}, status=status.HTTP_200_OK)
    
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
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    
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
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def filter_circuits(request, user_id, spraywall_id):
    if request.method == 'GET':
        # get all circuits associated to that particular user and spraywall
        circuits = Circuit.objects.filter(person=user_id, spraywall=spraywall_id)
        data = []
        for circuit in circuits:
            data.append({
                'id': circuit.id,
                'name': circuit.name,
                'description': circuit.description,
                'color': circuit.color,
                'private': circuit.private,
            })
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token, 'data': data}, status=status.HTTP_200_OK)
