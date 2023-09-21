from .common_imports import *

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

def add_activity(model_name, model_id, action, item, other_info, spraywall, user):
    data = {
        model_name: model_id,
        'action': action,
        'item': item,
        'other_info': other_info,
        'spraywall': spraywall,
        'person': user
    }
    activity_serializer = ActivitySerializer(data=data)
    if activity_serializer.is_valid():
        activity_serializer.save()
    else:
        print(activity_serializer.errors)

def get_boulder_data(boulder, user_id):
    return {
        'id': boulder.id,
        'uuid': uuid.uuid4(),
        'name': boulder.name,
        'description': boulder.description,
        'url': boulder.boulder_image_url,
        'width': boulder.boulder_image_width,
        'height': boulder.boulder_image_height,
        'matching': boulder.matching,
        'publish': boulder.publish,
        'feetFollowHands': boulder.feet_follow_hands,
        'kickboardOn': boulder.kickboard_on,
        'setter': boulder.setter_person.username,
        'firstAscent': boulder.first_ascent_person.username if boulder.first_ascent_person else None,
        'sends': boulder.sends_count,
        'grade': boulder.grade,
        'quality': boulder.quality,
        'isLiked': Like.objects.filter(person=user_id, boulder=boulder).exists(),
        'isBookmarked': Bookmark.objects.filter(person=user_id, boulder=boulder).exists(),
        'isSent': Send.objects.filter(person=user_id, boulder=boulder).exists(),
        'inCircuit': Circuit.objects.filter(boulders=boulder, person=user_id).exists(),
        'userSendsCount': boulder.send_set.filter(person=user_id).count(),
        'date': DateFormat(boulder.date_created).format('F j, Y'),
    }

# no need for this???
def delete_activity(action, item, other_info, spraywall, user):
    # action and other_info are optional parameters!!
    # Start with a base query without specific conditions
    base_query = Q(item=item, spraywall=spraywall, person=user)

    # Check if action is not None, then add it to the query
    if action is not None:
        base_query &= Q(action=action)

    # Check if other_info is not None, then add it to the query
    if other_info is not None:
        base_query &= Q(other_info=other_info)

    # Execute the query
    activity_row = Activity.objects.filter(base_query)
    activity_row.delete()

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