from django.db import models
from ..user.models import Person
from ..boulder.models import Boulder

class Send(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    attempts = models.SmallIntegerField(default=1) # attempts are 1 - 100 so we can definitely use smallintegerfield
    suggested_grade = models.PositiveIntegerField(blank=True, null=True) 
    quality = models.SmallIntegerField(default=3)
    notes = models.TextField(blank=True, null=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE, db_index=True)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['person', 'boulder']),
        ]