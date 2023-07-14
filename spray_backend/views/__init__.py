from rest_framework.decorators import api_view
from spray_backend.forms import CreateUserForm
from spray_backend.serializers import GymSerializer, SprayWallSerializer, BoulderSerializer, PersonSerializer, LikeSerializer, SendSerializer, CircuitSerializer, BookmarkSerializer
from rest_framework.response import Response
from django.middleware.csrf import get_token
from rest_framework import status
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from spray_backend.models import Gym, SprayWall, Person, Boulder, Like, Send, Circuit, Bookmark
from PIL import Image, ImageEnhance
from spray_backend.utils.constants import boulder_grades, boulders_bar_chart_data, colors
from io import BytesIO
import json
import uuid
import base64
from urllib.parse import urlparse
import boto3
from botocore.exceptions import NoCredentialsError
import environ
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))

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

def base64_string_to_image(drawing, photo):
    drawing_image = Image.open(BytesIO(base64.b64decode(drawing)))
    photo_image = Image.open(BytesIO(base64.b64decode(photo)))
    return drawing_image, photo_image

def increase_drawing_opacity(drawing_image):
    # increase opacity of drawings, but NOT the transparent background
    # Split the image into channels 
    r, g, b, a = drawing_image.split()
    # Increase the opacity of the alpha channel
    # Multiplication - transparent alpha is 0 so it will stay 0
    # Multiply by 2.5 since we want to increase it by 2.5 to get 255. Our original opacity is 0.4, multiply that by 2.5 and we get 1
    a = a.point(lambda x: x * 2)
    # Merge the channels back into an RGBA image
    return Image.merge('RGBA', (r, g, b, a))

def mask_drawing(drawing_image, photo_image):
    # Create a blank white mask, same size, and gray-scaled (mode 'L')
    mask = Image.new("L", drawing_image.size, 'WHITE')
    # Paste our drawing over new blank mask, masking the drawings with the drawings themselves
    mask.paste(drawing_image, mask=drawing_image)
    # Cut out the photo where we drew using our drawing mask
    drawing_image = Image.composite(drawing_image, photo_image, mask)
    return drawing_image

def combine_images(drawing_image, photo_image):
    # gray-scale photo image, but before converting to 'L' mode, grab the alpha channel
    # converting to 'L' mode (Luminance) gray-scales image efficiently through a single 8-bit channel per pixel, rather than RGBA which provides 4 x 8-bit channels per pixel
    alpha_channel  = photo_image.getchannel('A')
    gray_channels = photo_image.convert('L')
    # convert back to RGBA but merge the gray channel values as 'RGB' and the original alpha channel for 'A', all as a tuple.
    photo_image_result = Image.merge('RGBA', (gray_channels, gray_channels, gray_channels, alpha_channel))
    # darken photo image background before alpha compositing the images together
    brightnessLevel = ImageEnhance.Brightness(photo_image_result)
    # factor > 1 brightens. factor < 1 darkens
    factor = 0.4
    photo_image_result = brightnessLevel.enhance(factor)
    # alpha composite to place drawing image on top of manipulated photo image
    photo_image_result.alpha_composite(drawing_image)
    return photo_image_result

def image_to_base64_string(result):
    buffered = BytesIO()
    result.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

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
            'url': boulder.boulder_image_url,
            'width': boulder.boulder_image_width,
            'height': boulder.boulder_image_height,
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