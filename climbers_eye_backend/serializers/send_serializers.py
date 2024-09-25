from rest_framework import serializers
from climbers_eye_backend.models import Send
from climbers_eye_backend.serializers.fields import GradeField

class SendList(serializers.ModelSerializer):
    suggestedGrade = GradeField(source='suggested_grade')
    class Meta:
        model = Send
        fields = '__all__'

class SendDetail(serializers.ModelSerializer):
    class Meta:
        model = Send
        fields = '__all__'
