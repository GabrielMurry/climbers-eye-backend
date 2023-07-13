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
from .helperFunctions.list import get_filter_queries, filter_by_search_query, filter_by_circuits, filter_by_sort_by, filter_by_status, filter_by_grades, get_boulder_data
from django.middleware.csrf import get_token
from django.db.models import Q, Count
from utils.constants import boulder_grades, boulders_bar_chart_data, colors
from io import BytesIO
import uuid
from urllib.parse import urlparse
from PIL import Image
import base64
import boto3
from botocore.exceptions import NoCredentialsError
s3 = boto3.client('s3', aws_access_key_id='AKIA24PWBGA5KVTRS7UR',
                  aws_secret_access_key='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')

def get_spraywalls(gym_id):
    spraywalls = SprayWall.objects.filter(gym__id=gym_id) # gym__id is used to specify the filter condition. It indicates that you want to filter the SprayWall objects based on the id of the related gym object.
    spraywalls_array = []
    for spraywall in spraywalls:
        spraywalls_array.append({
            'id': spraywall.id,
            'name': spraywall.name,
            'url': spraywall.spraywall_image_url,
            'width': spraywall.spraywall_image_width,
            'height': spraywall.spraywall_image_height,
        })
    return spraywalls_array

def s3_image_url(base64_image):
    try:
        # Decode the base64 image data
        image_data = base64.b64decode(base64_image)
        # Create a file-like object from the decoded image data
        image_file = BytesIO(image_data)
        # Generate a unique key or filename for the image in S3
        s3_key = f"images/{str(uuid.uuid4())}.jpg"
        # Upload the image data to your S3 bucket
        # image_file, bucket name, unique key or filename for image in s3
        s3.upload_fileobj(image_file, 'sprayimages', s3_key)
        # Construct the S3 URL for the uploaded image
        image_url = f"https://sprayimages.s3.amazonaws.com/{s3_key}"
        return image_url
    except NoCredentialsError:
        # Handle the case where AWS credentials are missing or incorrect
        # Log the error or provide an appropriate error message
        error_message = "AWS credentials are missing or incorrect."
        print(error_message)
    except Exception as e:
        # Handle any other exceptions that may occur during the upload process
        # Log the error or provide an appropriate error message
        error_message = str(e)
        print(error_message)

def delete_image_from_s3(image_url):
    parsed_url = urlparse(image_url)
    bucket_name = 'sprayimages'
    s3_key = parsed_url.path.lstrip('/')
    # Delete the object from the S3 bucket
    s3.delete_object(Bucket=bucket_name, Key=s3_key)
    
@api_view(['GET'])
def csrf_token_view(request):
    if request.method == 'GET':
        return Response({'csrfToken': get_token(request)})
    
@api_view(['POST'])
def signup_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.data)
        if form.is_valid():
            form.save()
            person_serializer = PersonSerializer(data=request.data)
            if person_serializer.is_valid():
                person_instance = person_serializer.save()
                username = request.data.get('username')
                user = {
                    'id': person_instance.id,
                    'name': username
                }
                data = {
                    'user': user
                }
                return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
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
            person = Person.objects.get(username=username)
            data = {}
            if person.gym_id:
                gym_id = person.gym_id
                spraywalls = get_spraywalls(gym_id)
                user = {
                    'id': person.id,
                    'name': username
                }
                gym = {
                    'id': person.gym_id,
                    'name': person.gym.name,
                    'location': person.gym.location,
                    'type': person.gym.type,
                }
                data = {
                    'user': user, 
                    'gym': gym,
                    'spraywalls': spraywalls, 
                    'headshotImageUri': "data:image/png;base64," + person.headshot_image_url if person.headshot_image_url else None, 
                    'headshotImageWidth': person.headshot_image_width, 
                    'headshotImageHeight': person.headshot_image_height, 
                    'bannerImageUri': "data:image/png;base64," + person.banner_image_url if person.banner_image_url else None, 
                    'bannerImageWidth': person.banner_image_width, 
                    'bannerImageHeight': person.banner_image_height
                }
            else:
                data = {
                    'userID': person.id, 
                    'headshotImageUri': "data:image/png;base64," + person.headshot_image_data, 
                    'headshotImageWidth': person.headshot_image_width, 
                    'headshotImageHeight': person.headshot_image_height, 
                    'bannerImageUri': "data:image/png;base64," + person.banner_image_data if person.banner_image_data else None, 
                    'bannerImageWidth': person.banner_image_width, 
                    'bannerImageHeight': person.banner_image_height
                }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
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
        gym = request.data.get('gym')
        gym_data = {
            'name': gym['name'],
            'location': gym['location'],
            'type': gym['type'],
        }
        gym_serializer = GymSerializer(data=gym_data)
        if gym_serializer.is_valid():
            gym_instance = gym_serializer.save() # Save the gym instance and get the saved object --> need the recently created gym's ID!
            # Add Spray Wall
            spraywall = request.data.get('spraywall')
            image_url = s3_image_url(spraywall['image_data'])
            spraywall_data = {
                'name': spraywall['name'],
                'spraywall_image_url': image_url,
                'spraywall_image_width': spraywall['image_width'],
                'spraywall_image_height': spraywall['image_height'],
                'gym': gym_instance.id,
            }
            spraywall_serializer = SprayWallSerializer(data=spraywall_data)
            if spraywall_serializer.is_valid():
                spraywall_instance = spraywall_serializer.save()
                # Update Person data: person's gym_id foreign key and spraywall_id foreign key --> signifies person's default Gym and Wall
                person = Person.objects.get(id=user_id)
                person_data = {
                    'gym': gym_instance.id,
                    'spraywall': spraywall_instance.id
                }
                person_serializer = PersonSerializer(instance=person, data=person_data, partial=True) # partial=True allows for partial updates
                if person_serializer.is_valid():
                    person_serializer.save()
                    return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
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
        gym_id = person.gym.id
        spraywalls = get_spraywalls(gym_id)
        data = {
            'spraywalls': spraywalls[0]
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        
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

@api_view(['POST', 'DELETE'])
def like_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        data = { 'person': user_id, 'boulder': boulder_id }
        like_serializer = LikeSerializer(data=data)
        if like_serializer.is_valid():
            like_serializer.save()
            data = {'isLiked': True}
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(like_serializer.errors)
    if request.method == 'DELETE':
        liked_row = Like.objects.filter(person=user_id, boulder=boulder_id)
        liked_row.delete()
        data = {'isLiked': False}
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST', 'DELETE'])
def bookmark_boulder(request, boulder_id, user_id):
    if request.method == 'POST':
        data = { 'person': user_id, 'boulder': boulder_id }
        bookmark_serializer = BookmarkSerializer(data=data)
        if bookmark_serializer.is_valid():
            bookmark_serializer.save()
            data = {'isBookmarked': True}
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(bookmark_serializer.errors)
    if request.method == 'DELETE':
        bookmark_row = Bookmark.objects.filter(person=user_id, boulder=boulder_id)
        bookmark_row.delete()
        data = {'isBookmarked': False}
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def sent_boulder(request, boulder_id):
    if request.method == 'POST':
        # post new row that details user's attempts, chosen difficulty, quality, and notes for a particular boulder
        # update new info for the actual Boulder --> ?
        send_serializer = SendSerializer(data=request.data)
        if send_serializer.is_valid():
            send_serializer.save()
            boulder = Boulder.objects.get(id=boulder_id)
            boulder.sends_count += 1
            boulder.grade = request.data.get('grade')
            boulder.quality = request.data.get('quality')
            if boulder.first_ascent_person is None:
                person = Person.objects.get(id=request.data.get('person'))
                boulder.first_ascent_person = person
            boulder.save()
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
        boulder_row.delete()
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
    
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
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def queried_gym_spraywall(request, gym_id):
    if request.method == 'GET':
        # get gym's spraywall image, width, and height to display on bottom sheet in map screen when user clicks on gym card
        spraywalls = get_spraywalls(gym_id)
        data = {
            'spraywalls': spraywalls
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
    
@api_view(['PUT'])
def choose_gym(request, user_id, gym_id):
    if request.method == 'PUT':
        # updating person's default gym 
        person_data = {
            'gym': gym_id,
        }
        person = Person.objects.get(id=user_id)
        # update or add user's new default gym and spraywall
        person_serializer = PersonSerializer(instance=person, data=person_data, partial=True)
        if person_serializer.is_valid():
            person_instance = person_serializer.save()
            person_updated = Person.objects.get(id=person_instance.id)
            gym = {
                'id': gym_id,
                'name': person_updated.gym.name,
                'location': person_updated.gym.location,
                'type': person_updated.gym.type,
            }
            spraywalls = get_spraywalls(gym_id)
            data = {
                'gym': gym,
                'spraywalls': spraywalls,
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(person_serializer.errors)

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
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
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
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(circuit_serializer.errors)

@api_view(['DELETE'])
def delete_circuit(request, user_id, spraywall_id, circuit_id):
    if request.method == 'DELETE':
        # deleting a user's particular circuit in a particular spraywall
        circuit_row = Circuit.objects.get(id=circuit_id, person=user_id, spraywall=spraywall_id)
        circuit_row.delete()
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
    
@api_view(['POST'])
def add_new_spraywall(request, gym_id):
    if request.method == 'POST':
        # Add New Spray Wall
        spraywall = request.data
        image_url = s3_image_url(spraywall['image_data'])
        spraywall_data = {
            'name': spraywall['name'],
            'spraywall_image_url': image_url,
            'spraywall_image_width': spraywall['image_width'],
            'spraywall_image_height': spraywall['image_height'],
            'gym': gym_id,
        }
        spraywall_serializer = SprayWallSerializer(data=spraywall_data)
        if spraywall_serializer.is_valid():
            spraywall_serializer.save()
            spraywalls = get_spraywalls(gym_id)
            data = {
                'spraywalls': spraywalls
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(spraywall_serializer.errors)

@api_view(['DELETE'])
def delete_spraywall(request, spraywall_id):
    if request.method == 'DELETE':
        # grab spraywall row
        spraywall_row = SprayWall.objects.get(id=spraywall_id)
        # delete spraywall image from amazon s3
        delete_image_from_s3(spraywall_row.spraywall_image_url)
        # delete spraywall row from postgresql 
        spraywall_row.delete()
        gym_id = spraywall_row.gym_id
        spraywalls = get_spraywalls(gym_id)
        data = {
            'spraywalls': spraywalls
        }
        return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def edit_gym(request, gym_id):
    if request.method == 'POST':
        gym = Gym.objects.get(id=gym_id)
        gym_serializer = GymSerializer(instance=gym, data=request.data, partial=True)
        if gym_serializer.is_valid():
            gym_instance = gym_serializer.save() # Save the gym instance and get the saved object
            gym = {
                'id': gym_instance.id,
                'name': gym_instance.name,
                'location': gym_instance.location,
                'type': gym_instance.type,
            }
            data = {
                'gym': gym
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(gym_serializer.errors)

@api_view(['POST'])
def edit_spraywall(request, spraywall_id):
    if request.method == 'POST':
        spraywall = SprayWall.objects.get(id=spraywall_id)
        spraywall_serializer = SprayWallSerializer(instance=spraywall, data=request.data, partial=True)
        if spraywall_serializer.is_valid():
            spraywall_instance = spraywall_serializer.save() # Save the gym instance and get the saved object
            gym_id = spraywall_instance.gym_id
            spraywalls = get_spraywalls(gym_id)
            data = {
                'spraywalls': spraywalls
            }
            return Response({'csrfToken': get_token(request), 'data': data}, status=status.HTTP_200_OK)
        else:
            print(spraywall_serializer.errors)