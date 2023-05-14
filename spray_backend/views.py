from django.http import Http404
from django.shortcuts import render
from spray_backend.models import Movie
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .helperFunctions.composite import base64_string_to_image, increase_drawing_opacity, mask_drawing, combine_images, image_to_base64_string

def movie(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    if movie is not None:
        return render(request, 'movies/movie.html', {'movie': movie})
    else:
        raise Http404('Movie does not exist')
    
@api_view(['GET', 'POST'])    
def composite(request):
    drawing_image, photo_image = base64_string_to_image(request.data.get('drawing'), request.data.get('photo'))
    drawing_image = increase_drawing_opacity(drawing_image)
    drawing_image = mask_drawing(drawing_image, photo_image)
    result = combine_images(drawing_image, photo_image)
    data_uri = 'data:image/png;base64,' + image_to_base64_string(result)
    return Response(data_uri)