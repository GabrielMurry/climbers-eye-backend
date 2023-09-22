from .common_functions import *

def prepare_new_spraywall_data(spraywall, gym_id):
    image_url = s3_image_url(spraywall['image_data'])
    return {
        'name': spraywall['name'],
        'spraywall_image_url': image_url,
        'spraywall_image_width': spraywall['image_width'],
        'spraywall_image_height': spraywall['image_height'],
        'gym': gym_id,
    }