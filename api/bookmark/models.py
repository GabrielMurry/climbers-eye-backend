from django.db import models
from ..auth.models import Person
from ..boulder.models import Boulder

class Bookmark(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE)
    # the unique_together attribute in the Meta class ensures that a person can only like a particular boulder once. If they try to like the same boulder again, it will raise a unique constraint violation error.
    class Meta:
        unique_together = ('person', 'boulder')