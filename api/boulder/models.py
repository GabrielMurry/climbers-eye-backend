from django.db import models
from ..spraywall.models import SprayWall
from ..auth.models import Person

class Boulder(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    matching = models.BooleanField(default=True)
    publish = models.BooleanField(default=True)
    feet_follow_hands = models.BooleanField(default=True) 
    kickboard_on = models.BooleanField(default=False) 
    grade = models.PositiveIntegerField(blank=True, null=True)
    quality = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    sends_count = models.PositiveIntegerField(default=0)
    image_url = models.TextField()
    image_width = models.CharField(max_length=10, default=1000)
    image_height = models.CharField(max_length=10, default=1000)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    # foreign keys
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE)
    setter = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='set_boulders') # when the setter user deletes their account, all their boulders get deleted
    first_ascensionist = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True, related_name='first_ascended_boulders') # when the first ascensionist deletes their account, their first ascensions go to null?