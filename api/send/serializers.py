from rest_framework import serializers
from .models import Send
from utils.fields import GradeField

class SendList(serializers.ModelSerializer):
    suggestedGrade = GradeField(source='suggested_grade')
    class Meta:
        model = Send
        fields = '__all__'

class SendDetail(serializers.ModelSerializer):
    class Meta:
        model = Send
        fields = '__all__'
