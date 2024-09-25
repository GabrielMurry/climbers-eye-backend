from rest_framework import serializers
from .models import Circuit
from ..boulder.models import Boulder

class CircuitSerializer(serializers.ModelSerializer):
    boulders = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Boulder.objects.all(),
        required=False,    # Makes the field optional
        allow_empty=True,  # Allows the list to be empty
        allow_null=True    # Allows the field to be null
    )

    class Meta:
        model = Circuit
        fields = '__all__'