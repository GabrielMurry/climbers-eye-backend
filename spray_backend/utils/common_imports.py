from spray_backend.models import Gym, SprayWall, Person, Boulder, Like, Send, Circuit, Bookmark, Activity
import uuid
from django.db.models import Q, Count, Max
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.middleware.csrf import get_token
from rest_framework import status
from spray_backend.serializers import GymSerializer, SprayWallSerializer, BoulderSerializer, PersonSerializer, LikeSerializer, SendSerializer, CircuitSerializer, BookmarkSerializer, ActivitySerializer
from urllib.parse import urlparse
import json
from botocore.exceptions import NoCredentialsError
from .constants import boulders_bar_chart_data_template
from django.utils.dateformat import DateFormat
from io import BytesIO
import base64
import copy
import boto3
import environ
from spray_backend.utils.constants import boulders_section_quick_data_template, stats_section_quick_data_template
env = environ.Env()
environ.Env.read_env()
s3 = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'))