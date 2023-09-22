from .common_imports import *
from .common_functions import *
from PIL import Image, ImageEnhance
from .constants import boulder_grades

def image_to_base64_string(result):
    buffered = BytesIO()
    result.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

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
        boulders = boulders.filter(grade__isnull=False)
        return boulders
    elif status == 'projects':
        boulders = boulders.filter(grade__isnull=True)
        return boulders
    elif status == 'drafts':
        boulders = boulders.filter(setter_person=user_id, publish=False)
        return boulders
    
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

def prepare_new_boulder_data(boulder, user_id, spraywall_id):
    return {
        'name': boulder['name'],
        'description': boulder['description'],
        'matching': boulder['matching'],
        'publish': boulder['publish'],
        'feet_follow_hands': boulder['feet_follow_hands'],
        'kickboard_on': boulder['kickboard_on'],
        'boulder_image_url': s3_image_url(boulder['image_data']),
        'boulder_image_width': boulder['image_width'],
        'boulder_image_height': boulder['image_height'],
        'spraywall': spraywall_id,
        'setter_person': user_id,
    }