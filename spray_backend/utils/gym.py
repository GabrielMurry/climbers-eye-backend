from .common_functions import *


def create_gym(gym_data):
    gym_serializer = GymSerializer(data=gym_data)
    if gym_serializer.is_valid():
        return gym_serializer.save()
    else:
        print(gym_serializer.errors)
        return None


def update_person_data(user_id, gym_instance, spraywall_instance):
    person = Person.objects.get(id=user_id)
    person_data = {
        'gym': gym_instance.id,
        'spraywall': spraywall_instance.id
    }
    person_serializer = PersonSerializer(
        instance=person, data=person_data, partial=True)
    if person_serializer.is_valid():
        person_serializer.save()
    else:
        print(person_serializer.errors)


def get_gym_data(gym):
    return {
        'id': gym.id,
        'name': gym.name,
        'location': gym.location,
        'type': gym.type,
    }


def delete_spraywall_data(spraywall):
    boulders = Boulder.objects.filter(spraywall=spraywall)
    for boulder in boulders:
        delete_image_from_s3(boulder.boulder_image_url)
        boulder.delete()
    delete_image_from_s3(spraywall.spraywall_image_url)
    spraywall.delete()


def delete_gym_data(gym):
    spraywalls = SprayWall.objects.filter(gym=gym)
    for spraywall in spraywalls:
        delete_spraywall_data(spraywall)
    gym.delete()
