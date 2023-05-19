from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .forms import CreateUserForm
from .models import SprayWall
from spray_backend.models import Movie
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import GymSerializer, SprayWallSerializer, BoulderSerializer, PersonSerializer
from .helperFunctions.composite import base64_string_to_image, increase_drawing_opacity, mask_drawing, combine_images, image_to_base64_string
from django.middleware.csrf import get_token

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
        print(csrf_token)
        return Response({'csrfToken': csrf_token})
    

@api_view(['POST'])
def signup_user(request):
    if request.method == 'POST':
        print(request.data)
        form = CreateUserForm(request.data)
        if form.is_valid():
            form.save()
            serializer = PersonSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response('Successful Signup!', status=status.HTTP_200_OK)

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response('Successful Login!', status=status.HTTP_200_OK)
        else:
            return Response('Username or password is incorrect')

@api_view(['GET'])
def logout_user(request):
    logout(request)
    return Response('logged out')
    
@api_view(['GET'])    
def composite(request):
    drawing_image, photo_image = base64_string_to_image(request.data.get('drawing'), request.data.get('photo'))
    drawing_image = increase_drawing_opacity(drawing_image)
    drawing_image = mask_drawing(drawing_image, photo_image)
    result = combine_images(drawing_image, photo_image)
    data_uri = 'data:image/png;base64,' + image_to_base64_string(result)
    return Response(data_uri)

@api_view(['POST'])
def gym(request):
    if request.method == 'POST':
        serializer = GymSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # pass data back in response
            return Response(serializer.data)
        
@api_view(['GET', 'POST'])
def spraywall(request):
    if request.method == 'POST':
        serializer = SprayWallSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # pass data back in response
            return Response('hi')
    if request.method == 'GET':
        print('hi')
        queryset = SprayWall.objects.filter(id=2)
        print(queryset)
        serializer = SprayWallSerializer(queryset, many=True)
        return Response(serializer.data)

@api_view(['POST'])
def boulder(request):
    if request.method == 'POST':
        serializer = BoulderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # pass data back in response
            return Response('hi') 