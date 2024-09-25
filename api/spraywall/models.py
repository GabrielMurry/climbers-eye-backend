from django.db import models
from ..gym.models import Gym

class SprayWall(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.TextField() 
    image_width = models.CharField(max_length=10, default=1000)
    image_height = models.CharField(max_length=10, default=1000)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, blank=True, null=True)
