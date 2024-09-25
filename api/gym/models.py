from django.db import models

class Gym(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    place_id = models.CharField(max_length=255, unique=True, blank=True, null=True) 
    type = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)