from rest_framework import serializers
from climbers_eye_backend import models

class CircuitSerializer(serializers.ModelSerializer):
    boulders = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=models.Boulder.objects.all(),
        required=False,    # Makes the field optional
        allow_empty=True,  # Allows the list to be empty
        allow_null=True    # Allows the field to be null
    )

    class Meta:
        model = models.Circuit
        fields = '__all__'