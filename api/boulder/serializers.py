from rest_framework import serializers
from django.utils.dateformat import DateFormat
from django.db.models import Count
from .models import Boulder
from ..spraywall.models import SprayWall
from ..send.models import Send
from ..user.models import Person
from ..circuit.models import Circuit
from utils.constants import grade_labels
from utils.fields import UrlField, GradeField
from utils.mixins import BoulderMixin
from utils.test import create_blurred_placeholder

class BoulderSerializer(serializers.ModelSerializer, BoulderMixin):
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
    userSendsCount = serializers.SerializerMethodField(read_only=True)
    grade = GradeField(read_only=True)
    date = serializers.DateTimeField(format='%B %d, %Y', source='date_created', read_only=True)
    spraywall = serializers.PrimaryKeyRelatedField(queryset=SprayWall.objects.all()) 
    setter = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all()) 
    firstAscensionist = serializers.CharField(source='first_ascensionist.username', read_only=True)

    class Meta:
        model = Boulder
        fields = [
            'id', 'name', 'description', 'url', 'width', 'height',
            'matching', 'publish', 'feetFollowHands', 'kickboardOn', 'sends', 'grade', 'quality', 'isLiked', 
            'isBookmarked', 'isSent', 'inCircuit', 'userSendsCount', 'date',
            'spraywall', 'setter', 'firstAscensionist'
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # print('hi')
        # print(instance.image_url)
        # if instance.name == 'Butter':
        #     blur = create_blurred_placeholder(instance.image_url)
        #     print(instance.name, blur)
        # Replace the setter ID with the username in the serialized representation
        representation['setter'] = instance.setter.username if instance.setter else None
        return representation

class BoulderDetailSerializer(serializers.ModelSerializer, BoulderMixin):
    boulderBarChartData = serializers.SerializerMethodField(read_only=True)
    userSendsData = serializers.SerializerMethodField(read_only=True)
    firstAscensionist = serializers.CharField(source='first_ascensionist.username', read_only=True)
    sends = serializers.IntegerField(source='sends_count', read_only=True)
    isSent = serializers.SerializerMethodField(read_only=True)
    inCircuit = serializers.SerializerMethodField(read_only=True)
    userSendsCount = serializers.SerializerMethodField(read_only=True)
    grade = GradeField(read_only=True)

    class Meta:
        model = Boulder
        fields = [
            'boulderBarChartData', 'userSendsData', 'firstAscensionist', 'sends',
            'isSent', 'inCircuit', 'userSendsCount', 'grade', 'quality'
        ]

    def get_boulderBarChartData(self, obj: Boulder):
        queryset = (
            Send.objects
            .filter(boulder=obj.id)
            .values('suggested_grade')
            .annotate(count=Count('suggested_grade'))
            .order_by('suggested_grade')
        )
        # Convert QuerySet to a dictionary
        suggested_grade_count_dict = {grade_labels[item['suggested_grade']]: item['count'] for item in queryset}
        data = []
        for grade in grade_labels:
            if grade in suggested_grade_count_dict:
                data.append({'label': grade, 'value': suggested_grade_count_dict[grade]})
            else:
                data.append({'label': grade, 'value': 0})
        return data

    def get_userSendsData(self, obj: Boulder):
        boulder = obj
        user_id = self.context['request'].user.id
        DATA = []
        sent_boulders = Send.objects.filter(
            boulder=boulder.id, person=user_id).order_by('-date_created')
        for sent_boulder in sent_boulders:
            DATA.append({
                'id': sent_boulder.id,
                'date': DateFormat(sent_boulder.date_created).format('F j, Y'),
                'attempts': sent_boulder.attempts,
                'grade': grade_labels[sent_boulder.suggested_grade],
                'quality': sent_boulder.quality,
                'notes': sent_boulder.notes
            })
        return DATA
    
    def get_isSent(self, obj: Boulder):
        user_id = self.context['request'].user.id
        return Send.objects.filter(boulder=obj.id, person=user_id).exists()
    
    def get_inCircuit(self, obj: Boulder):
        user_id = self.context['request'].user.id
        instance = Boulder.objects.get(id=obj.id)
        spraywall_id = instance.spraywall.id
        return Circuit.objects.filter(
            person=user_id,
            spraywall=spraywall_id,
            boulders__id=obj.id
        ).exists()