from django.db import models
from ..boulder.models import Boulder
from ..auth.models import Person
from ..spraywall.models import SprayWall

class Circuit(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, blank=True)
    private = models.BooleanField(default=False)
    boulders = models.ManyToManyField(Boulder, related_name='circuits') # Django automatically creates indexes for Many-to-Many fields
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE, db_index=True) # who this circuit belongs to
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE, blank=True, null=True) # which spraywall the circuit belongs to 