from .common_functions import *

def get_auth_user_data(user):
    return {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'email': user.email,
    }

def get_auth_gym_data(user):
    if user.gym_id:
        return {
            'id': user.gym_id,
            'name': user.gym.name,
            'location': user.gym.location,
            'type': user.gym.type,
        }
    return None

def get_auth_spraywalls_data(user):
    if user.gym_id:
        return get_spraywalls(user.gym_id)
    return None

def get_auth_headshot_data(user):
    return {
        'url': user.headshot_image_url if user.headshot_image_url else None,
        'width': user.headshot_image_width,
        'height': user.headshot_image_height,
    }