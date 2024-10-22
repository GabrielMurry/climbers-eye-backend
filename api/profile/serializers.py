from rest_framework import serializers
import uuid
from django.utils.dateformat import DateFormat
from django.db.models import Count
from ..boulder.models import Boulder
from ..spraywall.models import SprayWall
from ..send.models import Send
from ..user.models import Person
from utils.constants import grade_labels
from utils.fields import UrlField, GradeField
from utils.mixins import BoulderMixin

class LogbookSerializer(serializers.ModelSerializer, BoulderMixin):
    url = UrlField(source='image_url', required=True)
    width = serializers.CharField(source='image_width')
    height = serializers.CharField(source='image_height')
    matching = serializers.BooleanField()
    publish = serializers.BooleanField()
    feetFollowHands = serializers.BooleanField(source='feet_follow_hands')
    kickboardOn = serializers.BooleanField(source='kickboard_on')
    sends = serializers.IntegerField(source='sends_count', read_only=True)
    isLiked = serializers.BooleanField(source='is_liked', read_only=True)
    isBookmarked = serializers.BooleanField(source='is_bookmarked', read_only=True)
    isSent = serializers.BooleanField(source='is_sent', read_only=True)
    inCircuit = serializers.BooleanField(source='is_in_circuit', read_only=True)
    sendDate = serializers.DateTimeField(format='%B %d, %Y', source='send_date', read_only=True)
    userSendsCount = serializers.SerializerMethodField(read_only=True)
    grade = GradeField(read_only=True)
    date = serializers.DateTimeField(format='%B %d, %Y', source='date_created', read_only=True)
    spraywall = serializers.PrimaryKeyRelatedField(queryset=SprayWall.objects.all()) 
    setter = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all()) 
    firstAscensionist = serializers.CharField(source='first_ascensionist.username', read_only=True)
    # New UUID field
    unique_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Boulder
        fields = [
            'id', 'name', 'description', 'url', 'width', 'height',
            'matching', 'publish', 'feetFollowHands', 'kickboardOn', 'sends', 'grade', 'quality', 'isLiked', 
            'isBookmarked', 'isSent', 'inCircuit', 'sendDate', 'userSendsCount', 'date',
            'spraywall', 'setter', 'firstAscensionist', 'unique_id'
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Replace the setter ID with the username in the serialized representation
        representation['setter'] = instance.setter.username if instance.setter else None
        return representation
    
    def get_unique_id(self, obj):
        # Generate a new UUID for each serialized object
        return str(uuid.uuid4())